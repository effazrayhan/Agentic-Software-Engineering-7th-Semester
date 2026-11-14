import argparse
import json
import os
import re
import sqlite3
import sys
import time

import agent


def _to_number(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip().replace(",", "")
        m = re.fullmatch(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?", s)
        if m:
            try:
                return float(s)
            except Exception:
                return None
    return None


def is_correct(expected, actual, tol=1e-6):
    if expected == "CANNOT_ANSWER":
        if actual is None:
            return False
        return "CANNOT_ANSWER" in str(actual).upper()

    exp_num = _to_number(expected)
    act_num = _to_number(actual)
    if exp_num is not None and act_num is not None:
        return abs(exp_num - act_num) <= tol * max(1.0, abs(exp_num))

    # try to extract number from actual text if expected numeric
    if exp_num is not None and actual is not None:
        nums = re.findall(r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?", str(actual).replace(",", ""))
        for n in nums:
            try:
                if abs(float(n) - exp_num) <= tol * max(1.0, abs(exp_num)):
                    return True
            except Exception:
                pass
        return False

    return str(expected).strip() == str(actual).strip()


def compute_expected(questions, db_path="data.db"):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        for q in questions:
            if q.get("expected") == "CANNOT_ANSWER" or q.get("expected_sql") is None:
                q["expected"] = "CANNOT_ANSWER"
                continue
            cur.execute(q["expected_sql"])
            row = cur.fetchone()
            val = row[0] if row else None
            # normalize ints/floats
            if isinstance(val, float):
                # keep reasonable precision; tests compare numbers
                if val.is_integer():
                    val = int(val)
                else:
                    val = round(val, 10)
            q["expected"] = val
        return questions
    finally:
        conn.close()


def compute_metrics(results_path):
    by_q = {}
    with open(results_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            qid = r.get("question_id") or r.get("id")
            by_q.setdefault(qid, []).append(bool(r.get("correct")))

    if not by_q:
        return {"pass@1": 0.0, "pass^3": 0.0, "n_questions": 0}

    per_q = []
    all3 = 0
    for qid, vals in by_q.items():
        per_q.append(sum(1 for v in vals if v) / len(vals))
        if len(vals) >= 3 and all(vals[:3]):
            all3 += 1
        elif vals and all(vals):
            # if fewer trials recorded but all pass, don't count as pass^3 unless 3
            pass
    pass_at_1 = sum(per_q) / len(per_q)
    # pass^3: fraction of questions where all 3 trials pass
    pass_pow_3 = all3 / len(by_q)
    return {"pass@1": pass_at_1, "pass^3": pass_pow_3, "n_questions": len(by_q)}


def run_eval(questions_path, db_path, out_path, trials=3, limit=None, question_ids=None):
    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
    if question_ids:
        wanted = set(question_ids)
        questions = [q for q in questions if q["id"] in wanted]
    if limit is not None:
        questions = questions[:limit]

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    # append if exists? spec says write one JSONL line per run; for fresh eval better overwrite when starting
    # but keep simple: append
    with open(out_path, "a", encoding="utf-8") as out:
        for q in questions:
            for trial in range(1, trials + 1):
                t0 = time.time()
                res = agent.run(q["question"], db_path=db_path)
                seconds = res.get("seconds", time.time() - t0)
                correct = is_correct(q.get("expected"), res.get("answer", ""))
                rec = {
                    "id": q["id"],
                    "question_id": q["id"],
                    "trial": trial,
                    "question": q["question"],
                    "type": q.get("type"),
                    "expected": q.get("expected"),
                    "tool_calls": res.get("tool_calls", []),
                    "sql_written": res.get("sql_written", []),
                    "final_answer": res.get("answer", ""),
                    "status": res.get("status"),
                    "tokens": res.get("tokens", 0),
                    "seconds": seconds,
                    "correct": bool(correct),
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                print(f"{q['id']} trial {trial}: status={res.get('status')} correct={correct}")
    metrics = compute_metrics(out_path)
    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default="questions.json")
    ap.add_argument("--db", default="data.db")
    ap.add_argument("--compute-expected", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="run 2 questions, 1 trial each")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--out", default="eval_results.jsonl")
    ap.add_argument("--metrics", default=None, help="compute metrics from existing jsonl")
    args = ap.parse_args()

    if args.compute_expected:
        with open(args.questions, "r", encoding="utf-8") as f:
            questions = json.load(f)
        compute_expected(questions, args.db)
        with open(args.questions, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Updated expected values in {args.questions}")
        return

    if args.metrics:
        m = compute_metrics(args.metrics)
        print(json.dumps(m, indent=2))
        return

    if args.smoke:
        # fresh output for smoke
        if os.path.exists(args.out):
            os.remove(args.out)
        m = run_eval(args.questions, args.db, args.out, trials=1, limit=2, question_ids=args.ids)
        print(json.dumps(m, indent=2))
        return

    if args.run:
        m = run_eval(args.questions, args.db, args.out, trials=args.trials, limit=args.limit, question_ids=args.ids)
        print(json.dumps(m, indent=2))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
