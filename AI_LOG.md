# AI Log

[Stage 0] WROTE: Scaffolded a1_sql_agent/ and a2_bangla/ (with tests/), added .gitignore, README skeleton, empty AI_LOG structure; wrote tests-only for llm clients (a1_sql_agent/tests/test_llm.py, a2_bangla/tests/test_llm.py) expecting injectable-transport Ollama /api/chat clients; did not implement llm.py yet.
[Stage 0] PROVED BY: a1_sql_agent/tests/test_llm.py and a2_bangla/tests/test_llm.py (currently failing with ModuleNotFoundError: No module named 'llm', as expected pre-implementation).
[Stage 0] I REVIEWED: 

[Stage 1] WROTE: Tests-only for A1 build_db (a1_sql_agent/tests/test_build_db.py): checks 4+ tables including customers/products/orders/order_items, 200+ orders, 500+ order_items, and deterministic rebuild (identical dumps) with same seed; no build_db.py implementation yet.
[Stage 1] PROVED BY: a1_sql_agent/tests/test_build_db.py (currently failing with ModuleNotFoundError: No module named 'build_db', as expected pre-implementation).
[Stage 1] I REVIEWED: 

[Stage 2] WROTE: Tests-only for A1 tools (a1_sql_agent/tests/test_tools.py): get_schema, run_sql accepts SELECT/WITH, rejects disallowed/multi/empty, row limit, clear error on bad SQL, read-only execution cannot write even if filter bypassed (expects raw readonly executor), calculator handles arithmetic/percent/difference and rejects unsafe; no tools.py implementation yet.
[Stage 2] PROVED BY: a1_sql_agent/tests/test_tools.py (currently failing with ModuleNotFoundError: No module named 'tools', as expected pre-implementation).
[Stage 2] I REVIEWED: 

[Stage 3] WROTE: Tiny-tool probe of qwen2.5:3b (native /api/chat tools) reported; tests-only for A1 agent (a1_sql_agent/tests/test_agent.py) using a FAKE Ollama client covering ok (tool call->final), step_cap, budget, SQL-error retry, and malformed-output no-crash with final status; no agent.py implementation yet.
[Stage 3] PROVED BY: a1_sql_agent/tests/test_agent.py (currently failing with ModuleNotFoundError: No module named 'agent', as expected pre-implementation) plus probe evidence of native tool-call support.
[Stage 3] I REVIEWED: 

[Stage 4] WROTE: Tests-only for A1 questions/eval (a1_sql_agent/tests/test_eval.py): compute-expected uses expected_sql against DB, numeric tolerance and CANNOT_ANSWER matching, pass@1 and pass^3 computed correctly from a fake JSONL results file; questions.json and eval.py not implemented yet.
[Stage 4] PROVED BY: a1_sql_agent/tests/test_eval.py (currently failing with ModuleNotFoundError: No module named 'eval', as expected pre-implementation).
[Stage 4] I REVIEWED: 


[Stage 5] WROTE: Started A1 full baseline eval (compute-expected; 3 trials x 17 questions -> baseline_eval.jsonl) and drafted report_a1.md with real partial metrics/notes (no fabricated numbers); full failure grouping and approved before/after change pending completed baseline results.
[Stage 5] PROVED BY: a1_sql_agent/baseline_eval.jsonl (partial/in-progress at time of writing) and a1_sql_agent/eval.py --metrics on that file; smoke_results.jsonl.
[Stage 5] I REVIEWED: 

[Stage 6] WROTE: Drafted a2_bangla/dataset.tsv (50 aligned EN/BN pairs across question,instruction,explanation,arithmetic,summarise,long) and a2_bangla/DATASET_REVIEW_NOTES.md listing least-certain pairs; dataset requires student review/approval of every Bangla line.
[Stage 6] PROVED BY: a2_bangla/dataset.tsv (51 lines incl. header) and a2_bangla/DATASET_REVIEW_NOTES.md; no automated meaning-proof (human review required).
[Stage 6] I REVIEWED: 

[Stage 7] WROTE: Implemented a2_bangla/counter.py (count_tokens with injectable client, fixed system prompt, keep_alive=0, baseline, cache check, cost_usd) and tests/test_counter.py.
[Stage 7] PROVED BY: a2_bangla/tests/test_counter.py (tokens from prompt_eval_count/eval_count, cost 1M+1M=$0.75, baseline 'hi', cache mismatch/missing flags, keep_alive=0) — passing.
[Stage 7] I REVIEWED: 

[Stage 8] WROTE: Implemented a2_bangla/runner.py and tests/test_runner.py; ran real baseline+cache check (baseline_and_cache.json) and started 3-pair smoke run to smoke_results.csv (partial at time of writing).
[Stage 8] PROVED BY: a2_bangla/tests/test_runner.py (identical settings, required columns, resume) — passing; a2_bangla/baseline_and_cache.json (cache ok, identical prompt_eval_count) and a2_bangla/smoke_results.csv (real model outputs).
[Stage 8] I REVIEWED: 

[Stage 9] WROTE: Implemented a2_bangla/analyze.py and tests/test_analyze.py; generated smoke_comparison.csv and smoke analysis summary from real smoke results; drafted report_a2.md with real smoke/baseline numbers and TODOs for full run, chart (matplotlib unavailable in env), 10-pair quality check and surprising-prompt explanation.
[Stage 9] PROVED BY: a2_bangla/tests/test_analyze.py (ratios/totals/stats and deterministic bootstrap CI bracketing mean) — passing; a2_bangla/smoke_comparison.csv and analyze output from smoke_results.csv.
[Stage 9] I REVIEWED: 

[Stage 10] WROTE: Updated README.md with setup/tests/reproduce commands and artifact layout; added report_a1.md and report_a2.md drafts (real numbers only where available, TODOs elsewhere); re-ran all unit tests (A1: 20 OK, A2: 13 OK).
[Stage 10] PROVED BY: `cd a1_sql_agent && python3 -m unittest discover -s tests -v` (20 tests OK) and `cd a2_bangla && python3 -m unittest discover -s tests -v` (13 tests OK); presence of README/report files and reproducible commands.
[Stage 10] I REVIEWED: 

[Stage 11] WROTE: Scaffolded week-02/ (agentlab/, notices/, tests/) for the Week 02 assignment on branch assignment-2; confirmed Ollama is unreachable and no ollama binary is installed, so no real model runs or model-config lookup are possible yet.
[Stage 11] PROVED BY: `curl -s http://localhost:11434/api/tags` returned nothing and `which ollama` found no binary; empty week-02/ subdirectories created.
[Stage 11] I REVIEWED: 

[Stage 12] WROTE: Tests-only for Week 02 task 1 and the class-1 ledger stand-in: week-02/tests/test_kv_cache.py (Qwen2.5-7B config 28/4/128, bytes/token, 8k=448 MiB, 32k=1792 MiB, linear scaling) and week-02/tests/test_ledger.py ($0.15/$0.60 per million, accumulation, custom rates); no kv_cache.py or agentlab/lm.py implementation yet.
[Stage 12] PROVED BY: `cd week-02 && python3 -m unittest discover -s tests -v` — 2 errors, both ModuleNotFoundError (kv_cache, agentlab.lm), as expected before implementation.
[Stage 12] I REVIEWED: 

[Stage 13] WROTE: Implemented week-02/kv_cache.py (Qwen2.5-7B config, bytes-per-token formula) and week-02/agentlab/lm.py (class-1 ledger stand-in) plus kv_answer_key.json, explicitly marked as a self-derived stand-in because no official key was supplied.
[Stage 13] PROVED BY: `cd week-02 && python3 -m unittest discover -s tests -v` — 7 tests OK; answer-key cross-check confirmed 8192 and 32768 token byte counts match.
[Stage 13] I REVIEWED: 

[Stage 14] WROTE: Tests-only for the Week 02 notice corpus/schema stand-ins: week-02/tests/test_notices.py checks 50 unique notices with text, an explicit synthetic-source flag, a versioned schema, and validation of valid/unknown-type/missing-field/wrong-version records; no corpus or schema implementation yet.
[Stage 14] PROVED BY: `cd week-02 && python3 -m unittest discover -s tests -v` — 7 existing tests OK and test_notices fails with ImportError (SCHEMA_VERSION missing), as expected pre-implementation.
[Stage 14] I REVIEWED: 

[Stage 15] WROTE: Implemented week-02/notices/ (__init__.py loaders/validator, corpus.json with 50 synthetic domain notices clearly flagged as stand-ins, schema_v1.json with schema_version const and enums).
[Stage 15] PROVED BY: `cd week-02 && python3 -m unittest discover -s tests -v` — 15 tests OK (50 unique notices, synthetic flag, versioned schema, valid/invalid records).
[Stage 15] I REVIEWED: 

[Stage 16] WROTE: Tests-only for week-02/extract.py: fake backend checks 3 runs x 2 approaches per notice (300 calls for 50 notices), schema passed only to grammar calls with identical system prompt/prompt, ledger prices every call, required result columns, invalid output recorded without crashing, fenced JSON accepted, summarize compares valid counts and cost; no implementation yet.
[Stage 16] PROVED BY: `cd week-02 && python3 -m unittest discover -s tests -v` — 15 existing tests OK and test_extract fails with ModuleNotFoundError: No module named 'extract', as expected pre-implementation.
[Stage 16] I REVIEWED: 

[Stage 17] WROTE: Implemented week-02/extract.py (fixed system prompt, per-approach schema passing, JSON/fence parsing with validation, ledger-priced rows, summarize, Ollama chat backend with stream=False/keep_alive=0/temperature 0/seed 0/num_predict 256, and CLI writing results.jsonl + comparison.json).
[Stage 17] PROVED BY: `cd week-02 && python3 -m unittest discover -s tests -v` — 23 tests OK; `python3 extract.py --help` OK; monkeypatched-backend CLI self-check wrote 100 rows and a summary with 50 valid grammar records.
[Stage 17] I REVIEWED: 

[Stage 18] WROTE: Added week-02/README.md (setup, tests, KV-cache command, extraction command, stand-ins warning, model tag) and week-02/report.md (real KV-cache table with explicit missing-official-key note; extraction measures left as TODO because no real run exists), plus a pointer in the top-level README.
[Stage 18] PROVED BY: all suites re-run — A1 20 OK after `python3 build_db.py` (DB is gitignored/missing in this checkout), A2 13 OK, week-02 23 OK.
[Stage 18] I REVIEWED: 

[Stage 19] WROTE: Installed Ollama 0.40.16 locally under /tmp/opencode/ollama (official installer needed sudo), started the server, pulled qwen2.5:3b, updated week-02/report.md to record the real 2-call smoke test and current environment status; no code changes.
[Stage 19] PROVED BY: `/api/tags` lists qwen2.5:3b; week-02 unit tests 23 OK; real smoke run of one notice x 2 approaches produced 2 valid records (120 input / 91 output tokens each, $0.0000726 each).
[Stage 19] I REVIEWED: 
