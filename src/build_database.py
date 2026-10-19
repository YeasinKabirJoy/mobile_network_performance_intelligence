"""Build the Phase 4 SQLite analytical database from validated GeoParquet."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd


DEFAULT_INPUT = Path("data/processed/bgd_mobile_tiles_2024_q4_clean.parquet")
DEFAULT_SCHEMA = Path("sql/schema.sql")
DEFAULT_DATABASE = Path("data/processed/network_performance.sqlite")
DEFAULT_AUDIT = Path("reports/generated/sqlite_build_audit.json")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _nullable_int(value: object) -> int | None:
    return None if pd.isna(value) else int(value)


def build_database(input_path: Path, schema_path: Path, database_path: Path, audit_path: Path) -> dict:
    """Create a fresh validated SQLite database and atomically replace its output."""
    if not input_path.is_file() or not schema_path.is_file():
        raise FileNotFoundError("Processed input and SQL schema are required.")

    frame = gpd.read_parquet(input_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = database_path.with_suffix(".sqlite.tmp")
    if temporary_path.exists():
        temporary_path.unlink()

    connection = sqlite3.connect(temporary_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_path.read_text(encoding="utf-8"))

        regions = (
            frame[["adm1_iso", "adm1_name"]]
            .drop_duplicates()
            .sort_values("adm1_iso")
        )
        connection.executemany(
            "INSERT INTO dim_region (adm1_iso, adm1_name) VALUES (?, ?)",
            regions.itertuples(index=False, name=None),
        )

        insert_sql = """
        INSERT INTO fact_tile_performance (
            quadkey, period_start, year, quarter, quarter_label, source_layer,
            adm1_iso, tile_wkt, longitude, latitude,
            avg_d_kbps, avg_u_kbps, avg_d_mbps, avg_u_mbps,
            avg_lat_ms, avg_lat_down_ms, avg_lat_up_ms,
            tests, devices, measurement_volume, loaded_latency_complete,
            quality_note, boundary_ambiguous
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """
        rows = (
            (
                str(row.quadkey),
                row.period_start.strftime("%Y-%m-%d"),
                int(row.year),
                int(row.quarter),
                str(row.quarter_label),
                str(row.source_layer),
                str(row.adm1_iso),
                str(row.tile),
                float(row.tile_x),
                float(row.tile_y),
                int(row.avg_d_kbps),
                int(row.avg_u_kbps),
                float(row.avg_d_mbps),
                float(row.avg_u_mbps),
                int(row.avg_lat_ms),
                _nullable_int(row.avg_lat_down_ms),
                _nullable_int(row.avg_lat_up_ms),
                int(row.tests),
                int(row.devices),
                str(row.measurement_volume),
                int(row.loaded_latency_complete),
                str(row.quality_note),
                int(row.boundary_ambiguous),
            )
            for row in frame.itertuples(index=False)
        )
        connection.executemany(insert_sql, rows)

        metadata = {
            "dataset": "Speedtest by Ookla Global Mobile Network Performance Maps",
            "period": "2024-Q4",
            "geography": "Bangladesh ADM1 centroid assignment",
            "grain": "one quadkey per period_start",
            "database_engine": f"SQLite {sqlite3.sqlite_version}",
            "source_sha256": _sha256(input_path),
        }
        connection.executemany(
            "INSERT INTO project_metadata (metadata_key, metadata_value) VALUES (?, ?)",
            metadata.items(),
        )
        connection.commit()

        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        fact_rows = connection.execute("SELECT count(*) FROM fact_tile_performance").fetchone()[0]
        region_rows = connection.execute("SELECT count(*) FROM dim_region").fetchone()[0]
        key_rows = connection.execute(
            "SELECT count(*) FROM (SELECT quadkey, period_start FROM fact_tile_performance "
            "GROUP BY quadkey, period_start HAVING count(*) > 1)"
        ).fetchone()[0]
        if integrity != "ok" or foreign_key_errors or fact_rows != len(frame) or key_rows:
            raise ValueError("SQLite integrity, foreign-key, row-count, or grain validation failed.")
    finally:
        connection.close()

    temporary_path.replace(database_path)
    audit = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "sqlite_version": sqlite3.sqlite_version,
        "input_path": input_path.resolve().as_posix(),
        "database_path": database_path.resolve().as_posix(),
        "fact_rows": fact_rows,
        "region_rows": region_rows,
        "duplicate_tile_period_keys": key_rows,
        "integrity_check": integrity,
        "foreign_key_errors": len(foreign_key_errors),
        "database_size_bytes": database_path.stat().st_size,
        "database_sha256": _sha256(database_path),
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()
    print(json.dumps(build_database(args.input, args.schema, args.database, args.audit), indent=2))


if __name__ == "__main__":
    main()
