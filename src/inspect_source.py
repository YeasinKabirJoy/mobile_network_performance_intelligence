"""Inspect the Ookla Q4 2024 mobile Parquet source without transforming it.

Phase 1 only: this module records source metadata, schema, data-quality counts,
representative rows, and an approximate Bangladesh bounding-box coverage check.
It does not perform the precise country extraction or ADM1 assignment required
in Phase 2.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb


DEFAULT_SOURCE = Path("data/raw/2024-10-01_performance_mobile_tiles.parquet")
DEFAULT_BOUNDARY = Path("data/raw/geoBoundaries-BGD-ADM1.geojson")
DEFAULT_OUTPUT = Path("reports/generated/source_inspection.json")

# Conservative Bangladesh envelope used only to prove likely source coverage.
# Precise boundary filtering and ADM1 assignment belong to Phase 2.
BGD_BBOX = {"min_x": 88.0, "max_x": 92.8, "min_y": 20.5, "max_y": 26.7}


def _inside_ring(x: float, y: float, ring: list[list[float]]) -> bool:
    """Apply the ray-casting test to one closed GeoJSON linear ring."""
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous[:2]
        x2, y2 = current[:2]
        if (y1 > y) != (y2 > y):
            crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
        previous = current
    return inside


def _inside_polygon(x: float, y: float, polygon: list[list[list[float]]]) -> bool:
    """Return true when a point is in a polygon shell and outside every hole."""
    return _inside_ring(x, y, polygon[0]) and not any(
        _inside_ring(x, y, hole) for hole in polygon[1:]
    )


def _feature_contains(feature: dict, x: float, y: float) -> bool:
    geometry = feature["geometry"]
    polygons = (
        [geometry["coordinates"]]
        if geometry["type"] == "Polygon"
        else geometry["coordinates"]
    )
    return any(_inside_polygon(x, y, polygon) for polygon in polygons)


def inspect_source(source: Path, boundary: Path) -> dict:
    """Return reproducible metadata and quality evidence for a local Parquet file."""
    if not source.is_file():
        raise FileNotFoundError(
            f"Source file not found: {source}. Download the official file first."
        )
    if not boundary.is_file():
        raise FileNotFoundError(
            f"Boundary file not found: {boundary}. Download the official GeoJSON first."
        )

    connection = duckdb.connect()
    parquet_path = source.resolve().as_posix().replace("'", "''")
    relation = f"read_parquet('{parquet_path}')"

    schema_rows = connection.execute(f"DESCRIBE SELECT * FROM {relation}").fetchall()
    columns = [row[0] for row in schema_rows]
    required = {
        "quadkey",
        "tile_x",
        "tile_y",
        "avg_d_kbps",
        "avg_u_kbps",
        "avg_lat_ms",
        "tests",
        "devices",
    }
    missing = sorted(required.difference(columns))
    if missing:
        raise ValueError(f"Required source columns missing: {missing}")

    total_rows = connection.execute(f"SELECT count(*) FROM {relation}").fetchone()[0]
    duplicate_quadkeys = connection.execute(
        f"SELECT count(*) FROM (SELECT quadkey FROM {relation} "
        "GROUP BY quadkey HAVING count(*) > 1)"
    ).fetchone()[0]
    global_quality = connection.execute(
        f"""
        SELECT
            min(tile_x), max(tile_x), min(tile_y), max(tile_y),
            count(*) FILTER (WHERE tests <= 0),
            count(*) FILTER (WHERE devices <= 0),
            count(*) FILTER (WHERE tests < devices),
            count(*) FILTER (WHERE avg_d_kbps <= 0),
            count(*) FILTER (WHERE avg_u_kbps <= 0),
            count(*) FILTER (WHERE avg_lat_ms < 0)
        FROM {relation}
        """
    ).fetchone()

    null_expressions = ", ".join(
        f"count(*) FILTER (WHERE \"{name}\" IS NULL) AS \"{name}\""
        for name in columns
    )
    null_row = connection.execute(f"SELECT {null_expressions} FROM {relation}").fetchone()

    bbox = BGD_BBOX
    bbox_predicate = (
        f"tile_x BETWEEN {bbox['min_x']} AND {bbox['max_x']} AND "
        f"tile_y BETWEEN {bbox['min_y']} AND {bbox['max_y']}"
    )
    bbox_count = connection.execute(
        f"SELECT count(*) FROM {relation} WHERE {bbox_predicate}"
    ).fetchone()[0]
    bbox_summary = connection.execute(
        f"""
        SELECT
            min(tile_x), max(tile_x), min(tile_y), max(tile_y),
            sum(tests), sum(devices),
            min(avg_d_kbps), max(avg_d_kbps),
            min(avg_u_kbps), max(avg_u_kbps),
            min(avg_lat_ms), max(avg_lat_ms)
        FROM {relation}
        WHERE {bbox_predicate}
        """
    ).fetchone()
    sample_cursor = connection.execute(
        f"""
        SELECT quadkey, tile_x, tile_y, avg_d_kbps, avg_u_kbps,
               avg_lat_ms, avg_lat_down_ms, avg_lat_up_ms, tests, devices
        FROM {relation}
        WHERE {bbox_predicate}
        ORDER BY tests DESC, quadkey
        LIMIT 5
        """
    )
    sample_columns = [item[0] for item in sample_cursor.description]
    samples = [dict(zip(sample_columns, row)) for row in sample_cursor.fetchall()]

    boundary_data = json.loads(boundary.read_text(encoding="utf-8"))
    candidate_rows = connection.execute(
        f"""
        SELECT quadkey, tile_x, tile_y, avg_d_kbps, avg_u_kbps,
               avg_lat_ms, avg_lat_down_ms, avg_lat_up_ms, tests, devices
        FROM {relation}
        WHERE {bbox_predicate}
        """
    ).fetchall()
    exact_rows: list[tuple] = []
    division_counts: dict[str, int] = {}
    for row in candidate_rows:
        x, y = row[1], row[2]
        for feature in boundary_data["features"]:
            if _feature_contains(feature, x, y):
                exact_rows.append(row)
                division = feature["properties"]["shapeName"]
                division_counts[division] = division_counts.get(division, 0) + 1
                break
    exact_rows.sort(key=lambda row: (-row[8], row[0]))
    country_samples = [dict(zip(sample_columns, row)) for row in exact_rows[:5]]
    country_summary = {
        "tests": sum(row[8] for row in exact_rows),
        "devices": sum(row[9] for row in exact_rows),
        "missing_avg_lat_down_ms": sum(row[6] is None for row in exact_rows),
        "missing_avg_lat_up_ms": sum(row[7] is None for row in exact_rows),
        "tests_less_than_devices": sum(row[8] < row[9] for row in exact_rows),
    }

    return {
        "inspected_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_path": source.resolve().as_posix(),
        "file_size_bytes": source.stat().st_size,
        "row_count": total_rows,
        "schema": [
            {"name": row[0], "type": row[1], "nullable": row[2] == "YES"}
            for row in schema_rows
        ],
        "null_counts": dict(zip(columns, null_row)),
        "duplicate_quadkeys": duplicate_quadkeys,
        "global_quality_checks": dict(
            zip(
                [
                    "min_tile_x", "max_tile_x", "min_tile_y", "max_tile_y",
                    "nonpositive_tests", "nonpositive_devices",
                    "tests_less_than_devices", "nonpositive_avg_d_kbps",
                    "nonpositive_avg_u_kbps", "negative_avg_lat_ms",
                ],
                global_quality,
            )
        ),
        "bangladesh_bbox": bbox,
        "bangladesh_bbox_row_count": bbox_count,
        "bangladesh_bbox_summary": dict(
            zip(
                [
                    "min_tile_x", "max_tile_x", "min_tile_y", "max_tile_y",
                    "tests", "devices", "min_avg_d_kbps", "max_avg_d_kbps",
                    "min_avg_u_kbps", "max_avg_u_kbps", "min_avg_lat_ms",
                    "max_avg_lat_ms",
                ],
                bbox_summary,
            )
        ),
        "representative_bbox_rows": samples,
        "bangladesh_centroid_row_count": len(exact_rows),
        "bangladesh_centroid_rows_by_adm1": dict(sorted(division_counts.items())),
        "bangladesh_centroid_summary": country_summary,
        "representative_bangladesh_rows": country_samples,
        "boundary_path": boundary.resolve().as_posix(),
        "coverage_note": (
            "Point-in-polygon checks against official ADM1 geometry verify source "
            "coverage. This is inspection evidence only; audited extraction, border "
            "handling, geometry validation, and saved geographic outputs are Phase 2."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    result = inspect_source(args.source, args.boundary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
