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
