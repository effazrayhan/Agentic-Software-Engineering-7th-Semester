# Agentic Software Engineering, Part 1

Local-only assignments using Ollama (`qwen2.5:3b` at `http://localhost:11434`). No hosted APIs, no agent frameworks. Python 3 standard library only (exception: `matplotlib` allowed for the A2 chart; the included `chart.png` was generated without requiring it).

## Repository layout
- `a1_sql_agent/` — SQL calculation agent (SQLite + tool-using agent)
  - Code: `build_db.py`, `tools.py`, `agent.py`, `llm.py`, `eval.py`, `questions.json`
  - Tests: `tests/`
  - Artifacts: `smoke_results.jsonl`, `baseline_eval.jsonl` (partial in repo; full 3-trial run over 17 questions may need to be completed/regenerated)
  - Note: `data.db` is gitignored but rebuildable (`seed=42`)
- `a2_bangla/` — English vs Bangla token cost comparison
  - Code: `counter.py`, `runner.py`, `analyze.py`, `llm.py`
  - Data/tests: `dataset.tsv` (50 aligned pairs), `tests/` (fake backends)
  - Artifacts (included): `results.csv` (100 calls), `comparison.csv` (50 pairs), `chart.png`, `baseline_and_cache.json`, `smoke_results.csv`, `smoke_comparison.csv`
  - Reports/README: `report_a2.md`, `README.md`
- `AI_LOG.md` — per-stage work log
- `report_a1.md` — A1 report (draft; pending completed baseline + failure analysis/improvement)
- `report_a2.md` — A2 report (final short report based on included real run)
- `specs.md`, `01-assignments.pdf` — assignment materials

## Prerequisites
- Python 3
- [Ollama](https://ollama.com/) installed and running locally (`ollama serve` or the Ollama app)
- Model pulled locally: `qwen2.5:3b`
- (Optional) `matplotlib` if you want `analyze.py` to render charts directly in your environment

## Setup
```bash
ollama pull qwen2.5:3b
# verify Ollama is reachable and model is available
curl -s http://localhost:11434/api/tags
```

## Run tests (from repo root)
```bash
cd a1_sql_agent && python3 -m unittest discover -s tests -v
cd ../a2_bangla && python3 -m unittest discover -s tests -v
```
(Or run each command from the repo root by `cd`-ing into the respective folder as shown.)

## Reproduce

> Model runs produce real artifacts; reports must use numbers from real result files. Re-running with the model may yield different outputs/timings, but the methodology/settings are fixed as specified.

### Assignment 1 — DB, smoke, and evaluation
```bash
cd a1_sql_agent
python3 build_db.py                      # deterministic DB (seed=42)
python3 eval.py --compute-expected       # recompute expected values from expected_sql
python3 eval.py --smoke --out smoke_results.jsonl
python3 eval.py --run --trials 3 --out baseline_eval.jsonl
python3 eval.py --metrics baseline_eval.jsonl
```
- Included `baseline_eval.jsonl` may be partial; for a clean full baseline remove it first: `rm -f baseline_eval.jsonl`.
- `report_a1.md` requires completed baseline metrics plus Stage 5 failure analysis and an approved improvement with before/after numbers (from real runs).

### Assignment 2 — baseline/cache, run, and analysis
```bash
cd a2_bangla

# baseline + cache check (real model, keep_alive=0)
python3 - <<'PY'
import json, llm, counter
c = llm.OllamaClient()
b = counter.measure_baseline(c)
ok, a, b2, d = counter.check_cache(c)
with open('baseline_and_cache.json', 'w', encoding='utf-8') as f:
    json.dump({'baseline': b, 'cache_check': {'ok': ok, 'first': a, 'second': b2, 'details': d}}, f, ensure_ascii=False, indent=2)
print('cache_ok', ok, a, b2)
PY

# full 100-prompt run (50 pairs x 2), resumable
python3 runner.py --dataset dataset.tsv --out results.csv --num-predict 256 --seed 0 --temperature 0

# analysis -> comparison.csv and chart.png
python3 analyze.py --results results.csv --dataset dataset.tsv --comparison comparison.csv --chart chart.png
```
- Full-run artifacts (`results.csv`, `comparison.csv`, `chart.png`) and `report_a2.md` are included from a real run. To regenerate from scratch, remove/replace those outputs and rerun the commands above.
- Settings held constant for EN/BN: same fixed system prompt, temperature 0, fixed seed, `num_predict=256`, `keep_alive=0` on every call, no "answer in the same language" instruction.

## Notes
- `a1_sql_agent/data.db` is rebuildable from `build_db.py` and not committed.
- A2 cost model (notional): input $0.15 / 1M tokens, output $0.60 / 1M tokens.
- Do not fabricate results; update reports only from real result files (`baseline_eval.jsonl`, `results.csv`, `comparison.csv`, etc.). See `AI_LOG.md` for stage-by-stage entries.
