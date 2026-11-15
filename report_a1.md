# Assignment 1 Report — SQL Calculation Agent

**Model:** `qwen2.5:3b` (Ollama, `http://localhost:11434`)  
**Status:** **DRAFT / PARTIAL BASELINE** — metrics and failure analysis below are from the real but **incomplete** `a1_sql_agent/baseline_eval.jsonl` snapshot (34/51 runs: q01–q11 with 3 trials each, q12 with 1 trial; q13–q17 not yet run). Complete the full 17-question × 3-trial baseline and update this report with final numbers, any revised failure grouping, and approved before/after results.

## Architecture (summary)
- **DB:** `build_db.py` creates a deterministic SQLite DB (`random.seed(42)`) with 4 related tables (`customers`, `products`, `orders`, `order_items`), 200+ orders and 500+ order_items.
- **Tools:** `get_schema()`, `run_sql(query)` (read-only: `file:...?mode=ro` URI + `PRAGMA query_only=ON`; accepts only single `SELECT`/`WITH`; rejects DDL/DML/ATTACH/PRAGMA/multi-statement/empty; row limit via wrapping), `calculator(expr)` (safe AST-based arithmetic: `+ - * / **` and parentheses only).
- **Agent:** Hand-written loop in `agent.py` (no agent framework). Schema included in system prompt; model writes SQL as `run_sql` argument (one model call per step). Uses Ollama `/api/chat` with native `tools` (probe indicated reliable tool use for `qwen2.5:3b`). Caps: `MAX_STEPS`, token budget (sum of `prompt_eval_count + eval_count`). Per-run status: `ok | step_cap | budget | error`. Returns `{status, answer, tool_calls, sql_written, tokens, seconds}`. System prompt forbids invented numbers and requires `CANNOT_ANSWER` + short reason when DB cannot answer.
- **Evaluation:** `questions.json` (17 questions: simple/join/grouping/calculation/multi-tool/unanswerable). Expected values computed from `expected_sql` via `eval.py --compute-expected` (not taken from agent). `eval.py` runs trials and writes JSONL; metrics: `pass@1` (mean success per trial) and `pass^3` (fraction where all 3 trials pass), numeric tolerance and `CANNOT_ANSWER` matching.

## Baseline results (real, partial snapshot)
- **Source:** `a1_sql_agent/baseline_eval.jsonl` (incomplete: 34 runs, 12 questions recorded; q12 has trial 1 only, q13–q17 missing).
- **Metrics (`python3 eval.py --metrics baseline_eval.jsonl`):** `pass@1 = 0.6944444444444445`, `pass^3 = 0.5`, `n_questions = 12`.
- **Per-question (recorded):** all correct in recorded trials — q01,q02,q03,q04,q06,q08; failures in recorded trials — q05 (2/3), q07 (0/3), q09 (1/3), q10 (2/3), q11 (2/3), q12 (0/1).
- **Smoke run (`smoke_results.jsonl`, 2 questions, 1 trial):** q01 correct (`240` orders), q02 correct (`60` customers).

Commands to complete/regenerate a clean full baseline:
```bash
cd a1_sql_agent
python3 eval.py --compute-expected
rm -f baseline_eval.jsonl
python3 eval.py --run --trials 3 --out baseline_eval.jsonl
python3 eval.py --metrics baseline_eval.jsonl
```

## Failure analysis (3 most common types, from partial baseline)

1. **Wrong metric/entity counted (answers a different question than asked)**  
   - **Real example — q07 (join, expected `213`, 0/3 correct, statuses `ok,ok,ok`):** “How many order items are for products in the 'Electronics' category?”
   - **Observed behavior:** counted the wrong entity (distinct products / wrong filtered set) instead of order-item rows.
     - Trial 1: answered “17 distinct order items…” using `SELECT COUNT(DISTINCT id) FROM order_items WHERE id IN (SELECT id FROM products ... category = 'Electronics')`.
     - Trial 2: answered “17 order items…” using `SELECT COUNT(*) FROM products WHERE category = 'Electronics' AND id IN (SELECT DISTINCT product_id FROM order_items)` (counts products, not order items).
   - **Why it fails:** aggregation target does not match the asked entity (“order items”).

2. **Schema/relationship misunderstandings leading to invalid or misjoined queries (wasted steps/budget)**  
   - **Real example — q09 (grouping, expected `320`, 1/3 correct; statuses `ok,ok,budget`):** “What is the total quantity of items sold per category? Return the total quantity for category 'Books'.”
   - **Observed behavior:** guessed or confused columns/tables instead of grounding in the real schema.
     - Trial 1 (incorrect): answered `67` with wrong filters/joins (e.g. `o.products_id`, `p.name LIKE 'Books%'` instead of `p.category='Books'`).
     - Trial 3 (`budget`, incorrect): repeated invalid SQL against non-existent columns (e.g. `WHERE o.category = 'Books'`, `WHERE o.name = 'Books'`, `SUM oi.quantity` syntax issues) and exhausted the token budget.
   - **Why it fails:** not reliably using actual schema/relationships (`order_items` ↔ `products.category`) leads to errors/wrong results and lost budget.

3. **Hallucinated objects/incomplete recovery (non-existent tables/views, not grounded)**  
   - **Real example — q12 (calculation, expected `99.58`, 0/1 recorded, status `ok` but incorrect):** “What percentage of orders have a total value above the minimum order total? Return the percentage rounded to 2 decimal places.”
   - **Observed behavior:** assumed a non-existent object and did not recover with real tables.
     - SQL tried: `SELECT is_above_minimum FROM order_summary`
     - Final answer: explained the table does not exist but provided no correct computed percentage (incomplete).
   - **Why it fails:** hallucinated view (`order_summary`) instead of deriving the result from actual tables (`orders`/`order_items`).

*Other real errors consistent with these types in the snapshot: q05 trial 2 counted distinct customers (`12`) instead of orders (`48`); q10 trial 3 grouped by `orders.id`/misidentified customer → answered `6` vs `8`; q11 trial 2 used wrong column/denominator (`p.price`, wrong totals) → `5.89` vs `1862.17`.*

## Improvement (one change) — proposed, pending approval/rerun

**Proposed single change (not yet approved/applied):** strengthen grounding in the system prompt in `a1_sql_agent/agent.py` by (1) explicitly instructing the agent to inspect/call `get_schema` and use **only existing tables/columns**, and (2) adding a short few-shot example clarifying “count order items in a category” = count over `order_items` joined to `products` by `category` (not counting products), plus a reminder to derive results from real tables (no invented views like `order_summary`).

- **Targeted failures:** wrong entity counted (q07/q05), schema/column misjoins and budget waste (q09/q10/q11), hallucinated objects/incomplete recovery (q12).
- **Before (real, partial baseline):** `pass@1 = 0.6944444444444445`, `pass^3 = 0.5`, `n_questions = 12` (34-run snapshot of `baseline_eval.jsonl`).
- **After:** _TODO — record only after you approve this (or another single) change and a completed full 17×3 rerun; report before/after numbers from real result files (no fabrication)._

## Design-choice explanation
Schema-in-prompt + model-authored SQL passed to `run_sql` (one call/step) keeps the loop simple, lets the model adapt queries from tool feedback/errors, and avoids a rigid query planner while still enforcing correctness via read-only execution, constrained SQL, and answer-grounding rules. Native Ollama tool calling was selected based on a probe of `qwen2.5:3b`.

## Notes
- All numbers above come from real artifacts in this repo (`baseline_eval.jsonl`, `smoke_results.jsonl`); the baseline is **partial** and must be completed for final `pass@1`/`pass^3`, definitive failure grouping, and before/after improvement results.
- See `AI_LOG.md` for stage-by-stage work and proof.
