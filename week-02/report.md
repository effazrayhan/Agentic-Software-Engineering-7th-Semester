# Week 02 Report

## Stand-ins and limitations

No official KV-cache answer key, class-1 ledger, or classes 3-6 notice corpus was supplied. `kv_answer_key.json`, `agentlab/lm.py` and `notices/corpus.json` are self-created stand-ins and are flagged as such. A real 2-call smoke test with `qwen2.5:3b` passed on 19 Nov 2026 (one notice, both approaches, both records valid, 120 input / 91 output tokens each). The full 300-call run has not been executed, so the extraction numbers below are TODO, not estimates.

## Task 1 — KV-cache size of Qwen2.5-7B

Formula: `2 (K+V) x layers x kv_heads x head_dim x bytes_per_element x context_tokens`.
Config used: 28 layers, 4 KV heads, head_dim 128, fp16 (2 bytes) → 57,344 bytes per token.

| Context | Computed size | My derived key | Official answer key |
|---|---|---|---|
| 8k (8192) | 448 MiB (469,762,048 B) | 448 MiB | TODO — key not supplied |
| 32k (32768) | 1792 MiB = 1.75 GiB (1,879,048,192 B) | 1792 MiB | TODO — key not supplied |

The 32k cache is 4x the 8k cache, as expected from linear scaling.

## Task 2 — Notice extraction

- Corpus: 50 synthetic domain notices, flagged in `notices/corpus.json`; not the real course corpus.
- Schema: `schema_v1.json`, `schema_version` fixed at `1.0`, 7 required fields, enums for `notice_type` and `severity`.
- Approaches: prompt-only (schema described in the system prompt) vs grammar-constrained (same prompt, schema passed as Ollama `format`). Same system prompt, temperature 0, seed 0, `num_predict=256`, `keep_alive=0`.
- Runs: 3 per notice per approach = 300 calls.
- Ledger: stand-in at $0.15/M input and $0.60/M output; every call recorded in `results.jsonl`.

### Measures (fill from real `comparison.json` and `results.jsonl` only)

| Measure | Prompt-only | Grammar-constrained |
|---|---|---|
| Calls | TODO | TODO |
| Valid records / validity rate | TODO | TODO |
| Total input tokens | TODO | TODO |
| Total output tokens | TODO | TODO |
| Ledger cost (USD) | TODO | TODO |

### Quality check

TODO — compare extracted records against a sample of notices once real outputs exist.

### Surprising case

TODO — identify an extreme or unexpected result from the real run and explain it.

## What did not work

The system-installed Ollama service was unavailable (sudo required for the official installer), so Ollama 0.40.16 was installed locally under `/tmp/opencode/ollama` and `qwen2.5:3b` was pulled. The 2-call smoke test passed; the full 300-call run was deliberately not started. All extraction numbers remain TODO until that run is executed.
