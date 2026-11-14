# Assignment 2 — English vs Bangla Token Cost

Local comparison using Ollama (`qwen2.5:3b` at `http://localhost:11434`). Standard library only for code/tests/analysis logic (`chart.png` included; chart rendering can use `matplotlib` or another image tool if regenerated).

## Files
1. `dataset.tsv` — 50 aligned English/Bangla pairs
2. `counter.py`, `runner.py`, `llm.py`, `analyze.py` and `tests/` (fake backends for counting/cost/runner/analysis)
3. `results.csv` — 100 rows (one per call): `id,language,prompt,output,input_tokens,output_tokens,cost_usd,latency_s,done_reason`
4. `comparison.csv` — 50 rows (one per pair) with English/Bangla tokens and ratios
5. `report_a2.md` — short report with measures table, chart, and conclusions (`chart.png`)
6. This `README.md` — reproduction steps

Included artifacts from a real run: `baseline_and_cache.json`, `results.csv`, `comparison.csv`, `chart.png`, `smoke_results.csv`, `smoke_comparison.csv`.

## Setup
```bash
ollama pull qwen2.5:3b
# ensure Ollama is running, e.g. `ollama serve`
```

## Run tests
```bash
cd a2_bangla
python3 -m unittest discover -s tests -v
```

## Reproduce (from `a2_bangla/`)
```bash
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

# analysis + comparison table + chart
python3 analyze.py --results results.csv --dataset dataset.tsv --comparison comparison.csv --chart chart.png
```

## Method notes
- Identical settings for English/Bangla: same fixed system prompt, temperature `0`, fixed seed `0`, `num_predict=256`, `keep_alive=0` every call, no "answer in the same language" instruction.
- Notional cost: input $0.15 / 1M tokens, output $0.60 / 1M tokens.
- Real runs depend on local model/runtime; use numbers from real result files in reports. To regenerate from scratch, remove/replace `results.csv`, `comparison.csv`, and `chart.png` before rerunning.
