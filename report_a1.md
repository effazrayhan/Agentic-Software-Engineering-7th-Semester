# Assignment 1 Report — SQL Calculation Agent

**Model:** `qwen2.5:3b` (Ollama, `http://localhost:11434`)  
**Status:** **DRAFT / NOT FINAL** — based on partial run data available at generation time. Full 3-trial evaluation over all 17 questions was started but had not completed when this report was generated. Replace metrics and failure analysis with the final `baseline_eval.jsonl` results.

## Architecture (summary)
- **DB:** `build_db.py` creates a deterministic SQLite DB (`random.seed(42)`) with 4 related tables (`customers`, `products`, `orders`, `order_items`), 200+ orders and 500+ order_items.
- **Tools:** `get_schema()`, `run_sql(query)` (read-only: `file:...?mode=ro` URI + `PRAGMA query_only=ON`; accepts only single `SELECT`/`WITH`; rejects DDL/DML/ATTACH/PRAGMA/multi-statement/empty; row limit via wrapping), `calculator(expr)` (safe AST-based arithmetic: `+ - * / **` and parentheses only).
- **Agent:** Hand-written loop in `agent.py` (no agent framework). Schema included in system prompt; model writes SQL as `run_sql` argument (one model call per step). Uses Ollama `/api/chat` with native `tools` (probe indicated reliable tool use for `qwen2.5:3b`). Caps: `MAX_STEPS`, token budget (sum of `prompt_eval_count + eval_count`). Per-run status: `ok | step_cap | budget | error`. Returns `{status, answer, tool_calls, sql_written, tokens, seconds}`. System prompt forbids invented numbers and requires `CANNOT_ANSWER` + short reason when DB cannot answer.
- **Evaluation:** `questions.json` (17 questions: simple/join/grouping/calculation/multi-tool/unanswerable). Expected values computed from `expected_sql` via `eval.py --compute-expected` (not taken from agent). `eval.py` runs trials and writes JSONL; metrics: `pass@1` (mean success per trial) and `pass^3` (fraction where all 3 trials pass), numeric tolerance and `CANNOT_ANSWER` matching.

## Baseline results
- **Partial metrics (from `a1_sql_agent/baseline_eval.jsonl`, incomplete at generation time):** `pass@1 = 0.9444444444444445`, `pass^3 = 0.8333333333333334`, `n_questions = 6` (partial; **not the full 17-question/3-trial baseline**).
- **Smoke run (2 questions, 1 trial, `smoke_results.jsonl`):** `q01` correct (`240` orders), `q02` correct (`60` customers).
- **Full baseline:** _TODO — run to completion and record real metrics from final `baseline_eval.jsonl`._

Commands to produce full baseline:
```bash
cd a1_sql_agent
python3 eval.py --compute-expected
python3 eval.py --run --trials 3 --out baseline_eval.jsonl
python3 eval.py --metrics baseline_eval.jsonl
```

## Failure analysis (3 most common types)
_TODO — must be derived from the completed real baseline results file (group failures into 3 most common types with one real example each)._

## Improvement (one change, approved before rerun)
_TODO — propose ONE change after analyzing real baseline failures, get approval, rerun, and report before/after numbers._

## Design-choice explanation
Schema-in-prompt + model-authored SQL passed to `run_sql` (one call/step) keeps the loop simple, lets the model adapt queries from tool feedback/errors, and avoids a rigid query planner while still enforcing correctness via read-only execution, constrained SQL, and answer-grounding rules. Native Ollama tool calling was selected based on a probe of `qwen2.5:3b`.

## Notes
- Do not fabricate or replace numbers in this report; update only from real result files.
- See `AI_LOG.md` for stage-by-stage work and proof.
