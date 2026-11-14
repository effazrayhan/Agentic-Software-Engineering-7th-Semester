# Assignment 2 — English vs Bangla Token Cost

Model: `qwen2.5:3b` via Ollama (`http://localhost:11434`). Standard library only (+ `matplotlib`/ImageMagick used only to generate the chart image; analysis logic is in `analyze.py`).

## Files (submission)
1. `dataset.tsv` — 50 aligned English/Bangla pairs
2. `counter.py`, `runner.py` (+ `llm.py`, `analyze.py`) and tests in `tests/` (fake backends for counting/cost/runner/analysis)
3. `results.csv` — one row per call: `id,language,prompt,output,input_tokens,output_tokens,cost_usd,latency_s,done_reason`
4. `comparison.csv` — one row per pair with English/Bangla tokens and ratios
5. `report_a2.md` — short report with measures table, chart, conclusions (`chart.png`)
6. This `README.md` — reproduction steps

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

## Reproduce results
```bash
cd a2_bangla
# baseline + cache check (real model, keep_alive=0)
python3 - <<'PY'
import json,llm,counter
c=llm.OllamaClient()
b=counter.measure_baseline(c)
ok,a,b2,d=counter.check_cache(c)
open('baseline_and_cache.json','w',encoding='utf-8').write(json.dumps({'baseline':b,'cache_check':{'ok':ok,'first':a,'second':b2,'details':d}},ensure_ascii=False,indent=2))
print('cache_ok',ok,a,b2)
PY

# full 100-prompt run (50 pairs x 2), resumable
python3 runner.py --dataset dataset.tsv --out results.csv --num-predict 256 --seed 0 --temperature 0

# analysis + comparison table + chart
python3 analyze.py --results results.csv --dataset dataset.tsv --comparison comparison.csv --chart chart.png
```

Notes: identical settings for EN/BN, fixed system prompt, `keep_alive=0` per call, notional cost $0.15/1M input and $0.60/1M output. Real runs depend on local model/runtime; reports should use numbers from real result files only.
