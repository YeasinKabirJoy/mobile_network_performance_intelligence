"""Execute named Phase 4 SQLite queries and export reproducible CSV results."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DATABASE = Path("data/processed/network_performance.sqlite")
DEFAULT_SQL_FILES = [Path("sql/kpis.sql"), Path("sql/regional_analysis.sql")]
DEFAULT_OUTPUT_DIR = Path("reports/generated/sql")
DEFAULT_MANIFEST = Path("reports/generated/sql_query_manifest.json")
QUERY_PATTERN = re.compile(r"-- name:\s*([a-zA-Z0-9_]+)\s*\n(.*?);\s*(?=-- name:|\Z)", re.DOTALL)


def named_queries(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    queries = [(name, sql.strip()) for name, sql in QUERY_PATTERN.findall(text)]
    if not queries:
        raise ValueError(f"No named queries found in {path}")
    return queries


def run_queries(database: Path, sql_files: list[Path], output_dir: Path, manifest_path: Path) -> dict:
    if not database.is_file():
        raise FileNotFoundError(f"SQLite database not found: {database}")
    output_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True)
    outputs = []
    try:
        for sql_file in sql_files:
            for name, query in named_queries(sql_file):
                cursor = connection.execute(query)
                columns = [item[0] for item in cursor.description]
                rows = cursor.fetchall()
                output_path = output_dir / f"{name}.csv"
                with output_path.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(columns)
                    writer.writerows(rows)
                outputs.append(
                    {
                        "name": name,
                        "sql_file": sql_file.as_posix(),
                        "output": output_path.as_posix(),
                        "rows": len(rows),
                        "columns": columns,
                    }
                )
    finally:
        connection.close()

    manifest = {
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": database.resolve().as_posix(),
        "query_count": len(outputs),
        "queries": outputs,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("sql_files", nargs="*", type=Path, default=DEFAULT_SQL_FILES)
    args = parser.parse_args()
    print(json.dumps(run_queries(args.database, args.sql_files, args.output_dir, args.manifest), indent=2))


if __name__ == "__main__":
    main()
