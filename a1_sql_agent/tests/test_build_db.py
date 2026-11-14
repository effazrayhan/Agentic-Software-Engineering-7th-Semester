import os
import sqlite3
import tempfile
import unittest

import build_db


class TestBuildDB(unittest.TestCase):
    def _build(self, path):
        # expected API: build_db.build_database(path) or similar; support common names
        if hasattr(build_db, "build_database"):
            build_db.build_database(path)
        elif hasattr(build_db, "create_db"):
            build_db.create_db(path)
        elif hasattr(build_db, "main"):
            # allow main(db_path) or main() writing default; prefer explicit path
            try:
                build_db.main(path)
            except TypeError:
                old = os.getcwd()
                try:
                    os.chdir(os.path.dirname(path) or ".")
                    build_db.main()
                finally:
                    os.chdir(old)
        else:
            self.fail("build_db must expose build_database(db_path) (or create_db/main)")

    def test_build_creates_required_tables_and_rows(self):
        with tempfile.TemporaryDirectory() as d:
            db_path = os.path.join(d, "data.db")
            self._build(db_path)
            self.assertTrue(os.path.exists(db_path))
            conn = sqlite3.connect(db_path)
            try:
                cur = conn.cursor()
                tables = {
                    r[0]
                    for r in cur.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    ).fetchall()
                }
                self.assertGreaterEqual(len(tables), 4)
                for required in ("customers", "products", "orders", "order_items"):
                    self.assertIn(required, tables)

                orders = cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
                items = cur.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
                self.assertGreaterEqual(orders, 200)
                self.assertGreaterEqual(items, 500)
            finally:
                conn.close()

    def test_deterministic_rebuild_same_seed(self):
        with tempfile.TemporaryDirectory() as d:
            db1 = os.path.join(d, "a.db")
            db2 = os.path.join(d, "b.db")
            self._build(db1)
            self._build(db2)

            conn1 = sqlite3.connect(db1)
            conn2 = sqlite3.connect(db2)
            try:
                def dump(conn):
                    cur = conn.cursor()
                    tables = sorted(
                        r[0]
                        for r in cur.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                        ).fetchall()
                    )
                    out = {}
                    for t in tables:
                        cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
                        rows = cur.execute(f"SELECT * FROM {t} ORDER BY 1").fetchall()
                        out[t] = (cols, rows)
                    return out

                self.assertEqual(dump(conn1), dump(conn2))
            finally:
                conn1.close()
                conn2.close()


if __name__ == "__main__":
    unittest.main()
