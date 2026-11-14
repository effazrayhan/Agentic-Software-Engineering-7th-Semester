import os
import sqlite3
import tempfile
import unittest

import build_db
import tools


class TestTools(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "data.db")
        build_db.build_database(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_get_schema_includes_tables_and_columns(self):
        schema = tools.get_schema(self.db_path)
        self.assertIsInstance(schema, str)
        for t in ("customers", "products", "orders", "order_items"):
            self.assertIn(t, schema)
        # some column names
        for col in ("customer_id", "order_id", "price", "quantity"):
            self.assertIn(col, schema)

    def test_run_sql_accepts_select_and_with(self):
        out = tools.run_sql("SELECT COUNT(*) AS n FROM orders", self.db_path)
        self.assertIsInstance(out, str)
        self.assertIn("240", out)  # deterministic build
        out2 = tools.run_sql(
            "WITH c AS (SELECT 1 AS x) SELECT x FROM c", self.db_path
        )
        self.assertIn("1", out2)

    def test_run_sql_rejects_disallowed_and_multi_and_empty(self):
        bad_queries = [
            "DROP TABLE orders",
            "DELETE FROM orders",
            "UPDATE orders SET status='x'",
            "INSERT INTO customers(name,city,signup_date) VALUES ('a','b','c')",
            "ALTER TABLE orders ADD COLUMN x TEXT",
            "CREATE TABLE x(id INT)",
            "ATTACH DATABASE ':memory:' AS aux",
            "PRAGMA table_info(orders)",
            "SELECT 1; DROP TABLE orders",
            "   ",
            "",
        ]
        for q in bad_queries:
            out = tools.run_sql(q, self.db_path)
            self.assertIsInstance(out, str)
            self.assertTrue(
                "error" in out.lower() or "reject" in out.lower() or "not allowed" in out.lower() or "invalid" in out.lower(),
                msg=f"expected clear error for {q!r}, got {out!r}",
            )

    def test_run_sql_enforces_row_limit(self):
        # build many rows result via join/cartesian-like expansion; easier: select from order_items (>100 rows)
        out = tools.run_sql("SELECT id FROM order_items ORDER BY id", self.db_path)
        # should not return more than 100 data rows; allow header/formatting text but cap rows
        lines = [ln for ln in out.strip().splitlines() if ln.strip()]
        # representation may vary; enforce by checking it doesn't include a very high id that would appear if unlimited
        self.assertNotIn("500", out.split()[-1] if out.split() else "")
        self.assertLessEqual(len(lines), 120)  # generous for headers/separators

    def test_run_sql_bad_sql_returns_clear_error(self):
        out = tools.run_sql("SELECT * FROM no_such_table", self.db_path)
        self.assertIsInstance(out, str)
        self.assertTrue(
            "error" in out.lower() or "no such" in out.lower() or "fail" in out.lower(),
            msg=f"expected clear error string, got {out!r}",
        )

    def test_readonly_connection_cannot_write_even_if_filter_bypassed(self):
        # even if validation were bypassed, underlying execution must be read-only
        # try to find an internal raw executor; fall back to direct check expectation
        executor = None
        for name in ("_execute_readonly", "_run_readonly", "execute_readonly", "_execute_on_ro_connection"):
            if hasattr(tools, name):
                executor = getattr(tools, name)
                break
        self.assertIsNotNone(
            executor,
            "tools must expose a raw readonly executor (e.g. _execute_readonly) to prove writes fail even if filter bypassed",
        )
        with self.assertRaises(Exception):
            executor("INSERT INTO customers(name,city,signup_date) VALUES ('x','y','2020-01-01')", self.db_path)
        # db unchanged
        conn = sqlite3.connect(self.db_path)
        try:
            n = conn.execute("SELECT COUNT(*) FROM customers WHERE name='x'").fetchone()[0]
            self.assertEqual(n, 0)
        finally:
            conn.close()

    def test_calculator_basic_and_percent_difference(self):
        self.assertAlmostEqual(float(tools.calculator("2 + 3 * 4")), 14.0)
        self.assertAlmostEqual(float(tools.calculator("(10 - 5) / 5")), 1.0)
        self.assertAlmostEqual(float(tools.calculator("2 ** 3")), 8.0)
        # percent / difference cases (agent may compute like 15% of 200 or difference)
        self.assertAlmostEqual(float(tools.calculator("200 * 15 / 100")), 30.0)
        self.assertAlmostEqual(float(tools.calculator("150 - 120")), 30.0)
        self.assertAlmostEqual(float(tools.calculator("(150 - 120) / 120 * 100")), 25.0)

    def test_calculator_rejects_unsafe(self):
        unsafe = [
            "__import__('os').system('ls')",
            "open('x.txt','w').write('x')",
            "(lambda: 1)()",
            "1; 2",
            "abs(-1)",
            "x+1",
            "9//2",
        ]
        for expr in unsafe:
            out = tools.calculator(expr)
            # must not return a computed numeric success for unsafe/unsupported input; return clear error string
            if isinstance(out, (int, float)):
                self.fail(f"unsafe/unsupported expr {expr!r} must not return numeric result")
            self.assertIsInstance(out, str)
            self.assertTrue(
                "error" in out.lower() or "invalid" in out.lower() or "unsafe" in out.lower() or "not allowed" in out.lower(),
                msg=f"expected error for {expr!r}, got {out!r}",
            )


if __name__ == "__main__":
    unittest.main()
