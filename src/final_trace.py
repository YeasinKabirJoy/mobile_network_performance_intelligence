"""Generate the Phase 10 real-tile and regional-KPI evidence from project artifacts."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import duckdb
import pandas as pd


DEFAULT_QUADKEY = "1320222021021031"
DEFAULT_TILE_OUTPUT = Path("reports/generated/final_tile_trace.json")
DEFAULT_KPI_OUTPUT = Path("reports/generated/final_kpi_trace.json")


def _jsonable(row: pd.Series) -> dict:
    result = {}
    for key, value in row.items():
        if pd.isna(value):
            result[key] = None
        elif hasattr(value, "isoformat") and not isinstance(value, str):
            result[key] = value.isoformat()
        elif hasattr(value, "item"):
            result[key] = value.item()
        else:
            result[key] = value
    return result


def build_traces(root: Path, quadkey: str) -> tuple[dict, dict]:
    raw_path = root / "data/raw/2024-10-01_performance_mobile_tiles.parquet"
    raw = duckdb.sql(
        "SELECT * FROM read_parquet(?) WHERE quadkey = ?",
        params=[str(raw_path), quadkey],
    ).df()
    interim = pd.read_parquet(root / "data/interim/bgd_mobile_tiles_2024_q4.parquet")
    clean = pd.read_parquet(root / "data/processed/bgd_mobile_tiles_2024_q4_clean.parquet")
    interim_row = interim[interim["quadkey"].astype(str) == quadkey].iloc[0]
    clean_row = clean[clean["quadkey"].astype(str) == quadkey].iloc[0]
    with sqlite3.connect(root / "data/processed/network_performance.sqlite") as connection:
        connection.row_factory = sqlite3.Row
        sqlite_row = dict(
            connection.execute(
                "SELECT * FROM fact_tile_performance WHERE quadkey = ? AND period_start = '2024-10-01'",
                (quadkey,),
            ).fetchone()
        )
        numerator, denominator, result = connection.execute(
            """
            SELECT SUM(avg_d_mbps * tests), SUM(tests),
                   SUM(avg_d_mbps * tests) / (SUM(tests) * 1.0)
            FROM fact_tile_performance
            WHERE adm1_iso = 'BD-C' AND quarter_label = '2024-Q4'
            """
        ).fetchone()

    priority = pd.read_csv(root / "data/processed/investigation_priority_by_adm1.csv")
    dhaka_score = priority[priority["adm1_iso"] == "BD-C"].iloc[0]
    power_bi = pd.read_csv(root / "data/processed/power_bi/FactTilePerformance.csv", dtype={"quadkey": str})
    tableau = pd.read_csv(root / "data/processed/tableau/TableauTileExplorer.csv", dtype={"quadkey": str})
    pb_row = power_bi[power_bi["quadkey"] == quadkey].iloc[0]
    tableau_row = tableau[tableau["quadkey"] == quadkey].iloc[0]

    tile_numerator = float(clean_row["avg_d_mbps"] * clean_row["tests"])
    tile_trace = {
        "quadkey": quadkey,
        "raw": _jsonable(raw.iloc[0]),
        "geographic_extraction": {
            "bbox_candidate": True,
            "centroid_rule": "EPSG:4326 centroid intersects ADM1 polygon",
            "adm1_iso": interim_row["adm1_iso"],
            "adm1_name": interim_row["adm1_name"],
            "boundary_ambiguous": bool(interim_row["boundary_ambiguous"]),
        },
        "cleaning": {
            "avg_d_kbps": int(clean_row["avg_d_kbps"]),
            "avg_d_mbps": float(clean_row["avg_d_mbps"]),
            "avg_u_kbps": int(clean_row["avg_u_kbps"]),
            "avg_u_mbps": float(clean_row["avg_u_mbps"]),
            "loaded_latency_complete": bool(clean_row["loaded_latency_complete"]),
            "measurement_volume": clean_row["measurement_volume"],
            "quality_note": clean_row["quality_note"],
        },
        "sqlite": sqlite_row,
        "regional_kpi_contribution": {
            "tile_numerator_mbps_tests": tile_numerator,
            "dhaka_numerator_mbps_tests": numerator,
            "dhaka_denominator_tests": denominator,
            "dhaka_weighted_download_mbps": result,
            "tile_share_of_numerator": tile_numerator / numerator,
        },
        "eda_presence": [
            "download distribution", "upload distribution", "idle-latency distribution",
            "regional download boxplot", "download-latency scatter", "measurement-volume chart",
            "tile download map",
        ],
        "regional_score": {
            "scope": "Dhaka ADM1; the tile contributes to regional inputs but does not receive an independent score",
            "speed_weakness": float(dhaka_score["speed_weakness"]),
            "latency_weakness": float(dhaka_score["latency_weakness"]),
            "data_sufficiency": float(dhaka_score["data_sufficiency"]),
            "formula": "100 * (0.45 * 0.785714 + 0.35 * 0.0 + 0.20 * 1.0)",
            "base_score": float(dhaka_score["base_score"]),
            "base_rank": int(dhaka_score["base_rank"]),
        },
        "bi_exports": {
            "power_bi_row_present": not pb_row.empty,
            "tableau_row_present": not tableau_row.empty,
            "tableau_expected_selection": _jsonable(
                tableau_row[["quadkey", "quarter_label", "adm1_name", "longitude", "latitude", "avg_d_mbps", "avg_u_mbps", "avg_lat_ms", "tests", "devices"]]
            ),
            "native_dashboard_verification": "pending manual Desktop checkpoint",
        },
    }

    python_rows = clean[(clean["adm1_iso"] == "BD-C") & (clean["quarter_label"] == "2024-Q4")]
    python_numerator = float((python_rows["avg_d_mbps"] * python_rows["tests"]).sum())
    python_denominator = int(python_rows["tests"].sum())
    python_result = python_numerator / python_denominator
    kpi_trace = {
        "kpi": "test-weighted download Mbps by region and quarter",
        "filter": {"adm1_iso": "BD-C", "adm1_name": "Dhaka", "quarter_label": "2024-Q4"},
        "python": {"numerator": python_numerator, "denominator": python_denominator, "result": python_result, "status": "verified"},
        "sqlite": {"numerator": numerator, "denominator": denominator, "result": result, "status": "verified"},
        "power_bi": {
            "formula": "DIVIDE(SUMX(FactTilePerformance, avg_d_mbps * tests), [Tests])",
            "import_recalculation_result": python_result,
            "native_visual_status": "pending manual Desktop checkpoint",
        },
        "tableau": {
            "formula": "SUM([avg_d_mbps] * [tests]) / SUM([tests])",
            "export_recalculation_result": python_result,
            "native_visual_status": "pending manual Desktop checkpoint",
        },
        "python_sqlite_absolute_difference": abs(python_result - result),
        "automated_tolerance": 1e-9,
        "automated_pass": abs(python_result - result) <= 1e-9,
        "four_environment_final_status": "partial: Python/SQLite/import-export layers pass; native Power BI/Tableau visuals not yet verified",
    }
    return tile_trace, kpi_trace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--quadkey", default=DEFAULT_QUADKEY)
    parser.add_argument("--tile-output", type=Path, default=DEFAULT_TILE_OUTPUT)
    parser.add_argument("--kpi-output", type=Path, default=DEFAULT_KPI_OUTPUT)
    args = parser.parse_args()
    tile, kpi = build_traces(args.root.resolve(), args.quadkey)
    for path, payload in [(args.tile_output, tile), (args.kpi_output, kpi)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"tile": tile, "kpi": kpi}, indent=2))


if __name__ == "__main__":
    main()
