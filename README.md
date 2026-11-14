# Agentic Software Engineering, Part 1

Local-only assignments using Ollama (`qwen2.5:3b` at `http://localhost:11434`). No hosted APIs, no agent frameworks.

## Layout
- `a1_sql_agent/` — SQL calculation agent (SQLite + tool-using agent)
  - `build_db.py`, `data.db` (rebuildable), `tools.py`, `agent.py`, `llm.py`, `eval.py`, `questions.json`, `tests/`
  - artifacts: `smoke_results.jsonl`, `baseline_eval.jsonl` (when full run completes)
- `a2_bangla/` — English vs Bangla token cost comparison
  - `dataset.tsv` (draft, needs Bangla review/approval), `counter.py`, `runner.py`, `analyze.py`, `llm.py`, `tests/`
  - artifacts: `baseline_and_cache.json`, `smoke_results.csv`, `smoke_comparison.csv` (and full-run `results.csv`, `comparison.csv`, `chart.png` when produced)
- `AI_LOG.md` — per-stage work log
- `report_a1.md`, `report_a2.md` — reports (drafts; A1/A2 full numbers pending completed runs & approvals)
- `specs.md` — assignment spec

## Prerequisites
- Python 3
- [Ollama](https://ollama.com/) running locally
- Model: `qwen2.5:3b`
- Optional: `matplotlib` (for A2 category-ratio chart PNG)

## Setup
```bash
ollama pull qwen2.5:3b
# optional, for chart: python3 -m pip install --user matplotlib
```

## Tests
```bash
# Assignment 1 (from repo root)
cd a1_sql_agent && python -m unittest discover -s tests -v

# Assignment 2
cd ../a2_bangla && python -m unittest discover -s tests -v
```

## Reproduce
> Runs that call the model produce real, non-deterministic-in-time artifacts; numbers in reports must come from real result files.

### A1 — DB, tests, evaluation
```bash
cd a1_sql_agent
python3 build_db.py
python3 eval.py --compute-expected
python3 eval.py --smoke --out smoke_results.jsonl        # quick 2-question smoke
python3 eval.py --run --trials 3 --out baseline_eval.jsonl  # full baseline (student-run/long)
python3 eval.py --metrics baseline_eval.jsonl
```

### A2 — baseline/cache, smoke, full run, analysis
```bash
cd a2_bangla
# baseline + cache check (real model)
python3 -c "import json,llm,counter; c=llm.OllamaClient(); b=counter.measure_baseline(c); ok,a,b2,d=counter.check_cache(c); open('baseline_and_cache.json','w').write(json.dumps({'baseline':b,'cache_check':{'ok':ok,'first':a,'second':b2,'details':d}},ensure_ascii=False,indent=2))"

python3 runner.py --dataset dataset.tsv --out smoke_results.csv --limit-pairs 3 --num-predict 64  # smoke
python3 analyze.py --results smoke_results.csv --dataset dataset.tsv --comparison smoke_comparison.csv --chart smoke_chart.png

# full run (after dataset Bangla approval)
python3 runner.py --dataset dataset.tsv --out results.csv --num-predict 256 --seed 0 --temperature 0
python3 analyze.py --results results.csv --dataset dataset.tsv --comparison comparison.csv --chart chart.png
```

## Notes
- Standard library only (plus `matplotlib` for one chart in A2).
- DB is rebuildable from `a1_sql_agent/build_db.py` (`seed=42`).
- Large generated artifacts/models are not committed. Reports contain only numbers from real result files (drafts marked TODO where full runs/approvals pending).
