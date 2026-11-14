You are helping me with a university assignment, "Agentic Software Engineering, Part 1". I am the student; you are a coding assistant. Course rules: I must write or approve every test BEFORE the code, and keep a three-line log per piece of work. So you will work in STAGES and STOP at the end of each stage until I reply "approved, continue".

=== PROJECT ===
Two assignments in one repo. Both use a local model through Ollama: qwen2.5:3b at http://localhost:11434. No hosted APIs, no agent frameworks. Python 3, standard library only (sqlite3, urllib, json, csv, unittest, random, statistics, argparse). Exception: matplotlib is allowed for one chart in Assignment 2. Do not add other dependencies. Tests run with: python -m unittest discover -s tests -v (inside each assignment folder).

Layout:
  a1_sql_agent/  build_db.py tools.py agent.py llm.py eval.py questions.json tests/
  a2_bangla/     dataset.tsv counter.py runner.py analyze.py llm.py tests/
  AI_LOG.md  README.md  .gitignore  (report_a1.md and report_a2.md come later)

=== ASSIGNMENT 1: SQL calculation agent ===
- Agent answers calculation questions by calling tools; numbers must come from tool results, never from the model's own guesses.
- SQLite DB built by build_db.py with random.seed(42): at least 4 related tables (customers, products, orders, order_items), 200+ orders, 500+ order_items, deterministic (same seed = identical data).
- Tools: get_schema(); run_sql(query) (read-only executor); calculator(expr) (safe arithmetic, no eval on raw input, use ast-based evaluation of + - * / ** and parentheses only). Design choice: the schema goes into the system prompt and the agent writes the SQL as the run_sql argument (one model call per step). Document this in a comment at the top of agent.py.
- run_sql safety: open DB with sqlite3.connect("file:...?mode=ro", uri=True) AND PRAGMA query_only=ON; accept only a single statement starting with SELECT or WITH; reject DROP/DELETE/UPDATE/INSERT/ALTER/CREATE/ATTACH/PRAGMA, multiple statements, and empty input; apply a row limit of 100 by wrapping the query; return rows as text or a clear error message string (so the model can retry).
- Agent loop written by me/you, not a library: MAX_STEPS cap, token budget cap (sum of prompt_eval_count + eval_count from Ollama), and a final status per run: ok | step_cap | budget | error. Return a dict: status, answer, tool_calls, sql_written, tokens, seconds.
- Use Ollama /api/chat with the "tools" parameter. FIRST probe whether qwen2.5:3b handles a tiny tool call reliably. If not, fall back to asking for JSON {"tool": ..., "args": ...} and parse it. Tell me which you chose and why.
- System prompt must say: never invent numbers; if the database cannot answer, reply with the exact token CANNOT_ANSWER plus a short reason.
- Evaluation: questions.json with 17+ questions, each with id, question, type, expected (number or "CANNOT_ANSWER"), and expected_sql. Expected values are computed by running my own expected_sql against the DB (a script, eval.py --compute-expected), NEVER taken from the agent. Cover: simple, join, grouping, calculation (e.g. average order value and percent above minimum), at least 2 multi-tool-call questions, at least 2 unanswerable questions. Each question runs 3 trials. Write one JSONL line per run (question id, trial, tool calls, SQL, final answer, status, tokens, seconds, correct). Report pass@1 (mean success of a single trial) and pass^3 (fraction of questions where all 3 trials pass). Numeric answers are checked with a small tolerance; unanswerable ones by CANNOT_ANSWER.

=== ASSIGNMENT 2: English vs Bangla token cost ===
- dataset.tsv columns: id, category, english, bangla. 50 aligned pairs, categories: question, instruction, explanation, arithmetic, summarise, long (3-5 sentences). Vary length. Bangla must carry exactly the same meaning as the English: no extra detail, no missing detail.
- counter.py: a reusable function that calls Ollama and returns input tokens (prompt_eval_count), output tokens (eval_count), latency, done_reason and output text. The backend must be injectable so tests use a fake backend. Handle template overhead by using the SAME fixed system prompt for every call and measuring a baseline once with a tiny prompt ("hi") and recording it. Handle prompt caching by sending keep_alive: 0 on every call so each prompt runs in a fresh state, and add a check that runs one prompt twice and confirms prompt_eval_count is identical; if counts are missing or suspicious, flag them.
- Cost: input $0.15 per million tokens, output $0.60 per million tokens (notional).
- runner.py: sends all 50 English and 50 Bangla prompts with identical settings (model, temperature 0, fixed seed, num_predict e.g. 256, same system prompt, no "answer in the same language" instruction). Writes results.csv with columns: id, language, prompt, output, input_tokens, output_tokens, cost_usd, latency_s, done_reason. Resumable if interrupted.
- analyze.py: reads results.csv, writes comparison.csv (one row per pair: English and Bangla input/output tokens, input ratio, output ratio, total cost ratio). Reports totals, input cost ratio, total cost ratio, mean/median/min/max and a bootstrap 95% interval (10,000 resamples, fixed seed) of the per-pair ratio, latency per language, per-category ratios, and the largest-gap categories. Produces one chart (ratio per category or per pair) as PNG.

=== WORKING RULES (important) ===
1. Work one stage at a time, in the order below. At the end of each stage, STOP and print a short summary plus the exact command I should run.
2. TDD: in each stage, FIRST write the tests only, run them, and show me that they FAIL. Then STOP and wait for me to say "tests approved". Only after that, write the implementation, run the tests until they pass, and show me the diff summary. Do not write implementation and tests in the same step.
3. After each stage append a three-line entry to AI_LOG.md in this format:
   [Stage N] WROTE: <what you wrote>
   [Stage N] PROVED BY: <test names that prove it>
   [Stage N] I REVIEWED: <leave this line empty for the student to fill in>
4. Never fabricate numbers, results, outputs or report content. Reports must use only numbers from real result files. If something did not work, say so plainly.
5. Never change expected answers or tests to make the agent or code pass. If a test seems wrong, tell me and ask.
6. Do not run the long evaluation (Assignment 1 eval) or the full 100-prompt run (Assignment 2) yourself unless I ask; I run those in my own terminal. Short smoke tests (1-3 items) are fine.
7. Do not commit model files. Add .gitignore for __pycache__, *.pyc, .venv, and generated large files if needed. Keep the DB rebuildable from build_db.py.
8. Keep code simple and commented where the logic is non-obvious. The README must let someone reproduce everything in under 5 commands.
9. Before starting, check that Ollama is reachable and qwen2.5:3b is installed (call /api/tags). If not, tell me what to run.

=== STAGES ===
Stage 0: scaffold folders, .gitignore, empty AI_LOG.md, README skeleton, llm.py in each assignment (a minimal Ollama /api/chat client with injectable transport). Verify Ollama and the model are reachable.
Stage 1 (A1): build_db.py. Tests: deterministic output, 4+ tables, 200+ orders, 500+ order_items, rebuild gives identical data.
Stage 2 (A1): tools.py. Tests: get_schema; run_sql accepts SELECT and WITH; rejects DROP, DELETE, UPDATE, INSERT, ALTER, ATTACH, PRAGMA, "SELECT 1; DROP TABLE x", empty input; enforces row limit; returns a clear error string on bad SQL; the read-only connection cannot write even if the filter were bypassed; calculator handles percent/difference and rejects anything unsafe.
Stage 3 (A1): agent.py. First do the tiny-tool probe of qwen2.5:3b and report the result. Tests use a FAKE Ollama client: tool call then final answer gives status ok; endless tool calls give step_cap; token budget exceeded gives budget; SQL error is returned to the model and the model retries; malformed model output gives error or a retry, never a crash; the final status is always set.
Stage 4 (A1): questions.json (17+) and eval.py. Tests: compute-expected uses expected_sql, pass@1 and pass^3 are computed correctly from a fake results file, numeric tolerance, CANNOT_ANSWER matching. Then a smoke run on 2 questions only.
   --- I will run the full baseline eval myself, then come back with the numbers. ---
Stage 5 (A1): when I give you the baseline results file, group the failures into the 3 most common types with one real example each. Propose ONE change (e.g. sample rows in the schema prompt, few-shot examples, a stricter prompt) and wait for my approval. After I rerun, draft report_a1.md (architecture in a few lines, pass@1, pass^3, 3 failure types with examples, the change with before/after numbers, the design-choice explanation) using only real numbers.
Stage 6 (A2): draft dataset.tsv with 50 aligned pairs. STOP so I can review and correct EVERY Bangla line. Do not continue until I say the dataset is approved. Also write a short note listing which pairs you were least sure about.
Stage 7 (A2): counter.py and cost code. Tests with a FAKE backend: tokens read from prompt_eval_count/eval_count, cost arithmetic with known numbers (e.g. 1,000,000 in + 1,000,000 out = $0.75), baseline handling, cache check flags a mismatch, done_reason recorded.
Stage 8 (A2): runner.py. Tests with a fake backend: same settings for both languages, results.csv has the required columns, resume works. Then a smoke run of 3 pairs only and the baseline measurement.
   --- I will run the full 100-prompt run myself. ---
Stage 9 (A2): analyze.py. Tests on a small fake results.csv with hand-computed ratios: per-pair ratio, totals, mean/median/min/max, bootstrap interval is deterministic with the seed and brackets the mean. Then, after my real run, produce comparison.csv, the chart, and draft report_a2.md with a table of all measures and per-category gaps. Leave the 10-pair quality check and the "surprising prompt" explanation as clearly marked TODO sections for me to write after reading the outputs; you may suggest candidate pairs with extreme ratios.
Stage 10: finish both READMEs (setup, tests, run, reproduce numbers in under 5 commands, model tag qwen2.5:3b), re-run all tests, and go through the submission checklist: code runs, tests pass, data files included, run logs and results included, reports have numbers and the model tag, AI log present.

Start with Stage 0 now. Remember: tests first, then stop.
