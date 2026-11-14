"""
Design choice (A1 SQL agent):
- The database schema is included in the system prompt.
- The agent writes the SQL itself and passes it as the `run_sql` tool argument
  (one model call per step). Tool results (rows/errors) are fed back so the
  model can iterate or compute with `calculator`.
- Tool calling uses Ollama /api/chat with the native "tools" parameter (probe of
  qwen2.5:3b showed reliable tool_calls). The loop is hand-written (no agent
  library) with MAX_STEPS and token-budget caps.
"""

import json
import time

import llm
import tools

MAX_STEPS = 8
TOKEN_BUDGET = 4000

SYSTEM_PROMPT = (
    "You are a careful data assistant. Use the provided tools to answer questions "
    "about the SQLite database. Never invent numbers; every number in your answer "
    "must come from tool results. If the database cannot answer the question, reply "
    "with the exact token CANNOT_ANSWER plus a short reason.\n\n"
    "Database schema:\n{schema}"
)

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Return the database schema.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Run a read-only SQL query against the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL SELECT/WITH query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Safely evaluate an arithmetic expression (+ - * / ** and parentheses).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expr": {"type": "string", "description": "Arithmetic expression"}
                },
                "required": ["expr"],
            },
        },
    },
]


def _call_tool(name, arguments, db_path):
    args = arguments or {}
    if name == "get_schema":
        return tools.get_schema(db_path)
    if name == "run_sql":
        query = args.get("query") or args.get("sql") or ""
        return tools.run_sql(query, db_path)
    if name == "calculator":
        expr = args.get("expr") or args.get("expression") or ""
        return tools.calculator(expr)
    return f"Error: unknown tool {name}"


def run(question, db_path="data.db", client=None, max_steps=MAX_STEPS, token_budget=TOKEN_BUDGET):
    start = time.time()
    client = client or llm.OllamaClient()
    schema = tools.get_schema(db_path)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(schema=schema)},
        {"role": "user", "content": question},
    ]

    status = "error"
    answer = ""
    tool_calls_log = []
    sql_written = []
    tokens = 0
    steps = 0

    try:
        while True:
            if steps >= max_steps:
                status = "step_cap"
                break
            if tokens >= token_budget:
                status = "budget"
                break

            steps += 1
            try:
                resp = client.chat(messages=messages, tools=TOOL_DEFS)
            except Exception as e:
                status = "error"
                answer = f"Error: {e}"
                break

            tokens += int(resp.get("prompt_eval_count", 0) or 0) + int(
                resp.get("eval_count", 0) or 0
            )
            if tokens >= token_budget:
                status = "budget"
                break

            message = resp.get("message") or {}
            tcs = message.get("tool_calls") or []
            if tcs:
                # append assistant message with tool calls
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.get("content", "") or "",
                        "tool_calls": tcs,
                    }
                )
                for tc in tcs:
                    func = tc.get("function") or {}
                    name = func.get("name")
                    raw_args = func.get("arguments") or {}
                    if isinstance(raw_args, str):
                        try:
                            raw_args = json.loads(raw_args)
                        except Exception:
                            raw_args = {}
                    record = {"name": name, "arguments": raw_args}
                    tool_calls_log.append(record)
                    if name == "run_sql":
                        sql_written.append(raw_args.get("query") or raw_args.get("sql") or "")
                    result = _call_tool(name, raw_args, db_path)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id"),
                            "name": name,
                            "content": str(result),
                        }
                    )
                # continue loop for model to consume tool results
                continue

            # no tool calls: treat as final answer
            content = message.get("content")
            if content is None:
                content = ""
            answer = content
            status = "ok"
            break
    except Exception as e:
        status = "error"
        answer = f"Error: {e}"

    if not status:
        status = "error"
    return {
        "status": status,
        "answer": answer,
        "tool_calls": tool_calls_log,
        "sql_written": sql_written,
        "tokens": tokens,
        "seconds": time.time() - start,
    }
