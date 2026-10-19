"""Independently reconcile Phase 4 SQLite KPIs against Python calculations."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd


DEFAULT_PARQUET = Path("data/processed/bgd_mobile_tiles_2024_q4_clean.parquet")
DEFAULT_DATABASE = Path("data/processed/network_performance.sqlite")
DEFAULT_OUTPUT = Path("reports/generated/python_sql_reconciliation.json")


def python_kpis(parquet_path: Path) -> dict[str, float | int]:
    frame = gpd.read_parquet(parquet_path)
    tests = frame["tests"].astype(float)
    return {
        "tiles": len(frame),
        "tests": int(frame["tests"].sum()),
        "devices": int(frame["devices"].sum()),
        "tile_avg_download_mbps": float(frame["avg_d_mbps"].mean()),
        "test_weighted_download_mbps": float((frame["avg_d_mbps"] * tests).sum() / tests.sum()),
        "test_weighted_upload_mbps": float((frame["avg_u_mbps"] * tests).sum() / tests.sum()),
        "test_weighted_idle_latency_ms": float((frame["avg_lat_ms"] * tests).sum() / tests.sum()),
        "complete_loaded_latency_tiles": int(frame["loaded_latency_complete"].sum()),
    }


def sqlite_kpis(database_path: Path) -> dict[str, float | int]:
    query = """
    SELECT
        COUNT(*) AS tiles,
        SUM(tests) AS tests,
        SUM(devices) AS devices,
        AVG(avg_d_mbps) AS tile_avg_download_mbps,
        SUM(avg_d_mbps * tests) / SUM(tests) AS test_weighted_download_mbps,
        SUM(avg_u_mbps * tests) / SUM(tests) AS test_weighted_upload_mbps,
        SUM(avg_lat_ms * tests * 1.0) / SUM(tests) AS test_weighted_idle_latency_ms,
        SUM(loaded_latency_complete) AS complete_loaded_latency_tiles
    FROM fact_tile_performance
    """
    connection = sqlite3.connect(f"file:{database_path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        cursor = connection.execute(query)
        columns = [item[0] for item in cursor.description]
        return dict(zip(columns, cursor.fetchone()))
    finally:
        connection.close()


def reconcile(parquet_path: Path, database_path: Path, tolerance: float = 1e-9) -> dict:
    python_values = python_kpis(parquet_path)
    sql_values = sqlite_kpis(database_path)
    comparisons = []
    for metric, python_value in python_values.items():
        sql_value = sql_values[metric]
        difference = float(sql_value) - float(python_value)
        passed = math.isclose(float(sql_value), float(python_value), rel_tol=0, abs_tol=tolerance)
        comparisons.append(
            {
                "metric": metric,
                "python": python_value,
                "sqlite": sql_value,
                "difference": difference,
                "tolerance": tolerance,
                "passed": passed,
            }
        )
    return {
        "reconciled_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "All Q4 2024 retained Bangladesh tiles; no region filter",
        "comparisons": comparisons,
        "passed": all(item["passed"] for item in comparisons),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = reconcile(args.parquet, args.database)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
