# Week 02 Assignment — KV cache and notice extraction

Two tasks: (1) KV-cache size of Qwen2.5-7B at 8k and 32k tokens; (2) extract 50 notices into a versioned JSON schema, comparing prompt-only vs grammar-constrained over 3 runs each, priced through a class-1 ledger.

## Stand-ins (read this first)

No official answer key, class-1 ledger, or classes 3-6 notice corpus was provided with this repo. The following are clearly flagged stand-ins created for this work, not course originals:

- `kv_answer_key.json` — derived from published Qwen2.5-7B architecture (28 layers, 4 KV heads, head_dim 128, fp16).
- `agentlab/lm.py` — ledger at the Part 1 notional rates ($0.15/M input, $0.60/M output).
- `notices/corpus.json` — 50 synthetic domain notices (`source` field says so).

Replace these with the real course files if they become available; results must come from real runs, not from these stand-ins.

Model tag used for extraction: `qwen2.5:3b`. The KV-cache task is a calculation for `Qwen2.5-7B`.

## Setup

```bash
ollama serve
ollama pull qwen2.5:3b
```

## Tests

```bash
cd week-02 && python3 -m unittest discover -s tests -v
```

## KV-cache calculation

```bash
cd week-02 && python3 -c "import kv_cache as k; c=k.model_config('qwen2.5:7b'); print([(n, k.kv_cache_bytes(c,n)//1024**2) for n in (8192,32768)])"
```

## Extraction run (300 calls: 50 notices x 2 approaches x 3 runs)

```bash
cd week-02 && python3 extract.py --model qwen2.5:3b
```

Outputs: `results.jsonl` (one row per call) and `comparison.json` (per-approach validity and cost). Both are expected to be committed once produced from a real run.

## Files

- `kv_cache.py`, `kv_answer_key.json` — task 1 calculation and self-derived key.
- `notices/` — corpus, `schema_v1.json`, loaders and validator.
- `agentlab/lm.py` — ledger stand-in.
- `extract.py` — runner, Ollama backend, result writing.
- `tests/` — 23 unit tests using fake backends.
- `report.md` — report; extraction numbers are TODO until a real run exists.
