import ast
import operator
import re
import sqlite3

ROW_LIMIT = 100

_DISALLOWED = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|ATTACH|PRAGMA)\b", re.IGNORECASE
)


def get_schema(db_path="data.db"):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = conn.cursor()
        tables = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        lines = []
        for (t,) in tables:
            cols = cur.execute(f"PRAGMA table_info({t})").fetchall()
            col_desc = ", ".join(f"{c[1]} {c[2]}" for c in cols)
            lines.append(f"TABLE {t}({col_desc})")
        return "\n".join(lines)
    finally:
        conn.close()


def _open_readonly(db_path):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    return conn


def _execute_readonly(query, db_path="data.db"):
    """Execute SQL on a read-only connection without input validation (for safety proof)."""
    conn = _open_readonly(db_path)
    try:
        cur = conn.cursor()
        cur.execute(query)
        return cur.fetchall()
    finally:
        conn.close()


def _is_single_statement(sql):
    # strip trailing whitespace and a single trailing semicolon, then ensure no other semicolons
    s = sql.strip()
    if s.endswith(";"):
        s = s[:-1]
    return ";" not in s


def _strip_trailing_semicolon(sql):
    s = sql.strip()
    if s.endswith(";"):
        s = s[:-1].strip()
    return s


def run_sql(query, db_path="data.db"):
    if query is None or not str(query).strip():
        return "Error: empty input"

    q = str(query)
    if not _is_single_statement(q):
        return "Error: multiple statements are not allowed"

    q_stripped = _strip_trailing_semicolon(q)
    if not q_stripped:
        return "Error: empty input"

    first = re.match(r"^\s*(\w+)", q_stripped)
    if not first or first.group(1).upper() not in ("SELECT", "WITH"):
        return "Error: only SELECT or WITH statements are allowed"

    if _DISALLOWED.search(q_stripped):
        return "Error: disallowed SQL keyword"

    limited = f"SELECT * FROM ({q_stripped}) LIMIT {ROW_LIMIT}"
    conn = _open_readonly(db_path)
    try:
        cur = conn.cursor()
        cur.execute(limited)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        if not cols:
            return "(no rows)"
        header = " | ".join(cols)
        sep = "-" * len(header)
        lines = [header, sep]
        for r in rows:
            lines.append(" | ".join("" if v is None else str(v) for v in r))
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()


_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval_ast(node):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("unsupported expression")


def calculator(expr):
    try:
        if expr is None or not str(expr).strip():
            return "Error: empty expression"
        tree = ast.parse(str(expr), mode="eval")
        value = _eval_ast(tree)
        return str(value)
    except Exception as e:
        return f"Error: {e}"
