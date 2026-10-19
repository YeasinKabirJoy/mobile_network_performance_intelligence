import sqlite3
import unittest
from pathlib import Path

from src.run_sql import named_queries


class SqlAssetsTest(unittest.TestCase):
    def test_fifteen_named_queries_are_parseable(self):
        queries = named_queries(Path("sql/kpis.sql")) + named_queries(Path("sql/regional_analysis.sql"))
        self.assertEqual(len(queries), 15)
        self.assertEqual(len({name for name, _ in queries}), 15)

    def test_schema_enforces_fact_primary_key_and_foreign_key(self):
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(Path("sql/schema.sql").read_text(encoding="utf-8"))
        connection.execute("INSERT INTO dim_region VALUES ('BD-C', 'Dhaka')")
        values = (
            "q", "2024-10-01", 2024, 4, "2024-Q4", "performance_mobile_tiles",
            "BD-C", "POLYGON EMPTY", 90.0, 23.0, 1000, 500, 1.0, 0.5,
            20, None, None, 1, 1, "low", 0, "missing_loaded_latency", 0,
        )
        placeholders = ",".join("?" for _ in values)
        connection.execute(f"INSERT INTO fact_tile_performance VALUES ({placeholders})", values)
        with self.assertRaises(sqlite3.IntegrityError):
            connection.execute(f"INSERT INTO fact_tile_performance VALUES ({placeholders})", values)
        connection.close()


if __name__ == "__main__":
    unittest.main()
