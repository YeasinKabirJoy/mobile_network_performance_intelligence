"""Clean and validate the Bangladesh tile-per-quarter analytical dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from src.config import CLEANING, CleaningConfig


DEFAULT_INPUT = Path("data/interim/bgd_mobile_tiles_2024_q4.parquet")
DEFAULT_PARQUET = Path("data/processed/bgd_mobile_tiles_2024_q4_clean.parquet")
DEFAULT_CSV = Path("data/processed/bgd_mobile_tiles_2024_q4_clean.csv")
DEFAULT_AUDIT = Path("reports/generated/cleaning_audit.json")

REQUIRED_COLUMNS = {
    "quadkey",
    "tile",
    "tile_x",
    "tile_y",
    "avg_d_kbps",
    "avg_u_kbps",
    "avg_lat_ms",
    "avg_lat_down_ms",
    "avg_lat_up_ms",
    "tests",
    "devices",
    "geometry",
    "adm1_name",
    "adm1_iso",
    "period_start",
    "year",
    "quarter",
    "source_layer",
}
NON_NULL_COLUMNS = REQUIRED_COLUMNS.difference({"avg_lat_down_ms", "avg_lat_up_ms"})
INTEGER_COLUMNS = [
    "avg_d_kbps",
    "avg_u_kbps",
    "avg_lat_ms",
    "avg_lat_down_ms",
    "avg_lat_up_ms",
    "tests",
    "devices",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def clean_frame(frame: gpd.GeoDataFrame, config: CleaningConfig = CLEANING) -> tuple[gpd.GeoDataFrame, dict]:
    """Apply explicit validity rules and return the clean data plus an audit."""
    missing_columns = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"Required columns missing: {missing_columns}")
    if frame.crs is None or frame.crs.to_epsg() != 4326:
        raise ValueError(f"Expected EPSG:4326 input, received {frame.crs!s}")

    data = frame.copy()
    input_rows = len(data)
    input_columns = data.columns.tolist()
    nulls_before = {key: int(value) for key, value in data.isna().sum().items()}

    for column in INTEGER_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce").astype("Int64")
    data["tile_x"] = pd.to_numeric(data["tile_x"], errors="coerce")
    data["tile_y"] = pd.to_numeric(data["tile_y"], errors="coerce")
    data["period_start"] = pd.to_datetime(data["period_start"], errors="coerce")

    reasons = pd.DataFrame(index=data.index)
    reasons["missing_required"] = data[list(NON_NULL_COLUMNS)].isna().any(axis=1)
    reasons["duplicate_tile_period"] = data.duplicated(
        subset=["quadkey", "period_start"], keep=False
    )
    reasons["invalid_coordinates"] = (
        ~data["tile_x"].between(-180, 180)
        | ~data["tile_y"].between(-90, 90)
        | data.geometry.isna()
        | data.geometry.is_empty
    )
    reasons["centroid_coordinate_mismatch"] = (
        (data.geometry.x - data["tile_x"]).abs() > config.coordinate_tolerance
    ) | ((data.geometry.y - data["tile_y"]).abs() > config.coordinate_tolerance)
    reasons["invalid_counts"] = (
        (data["tests"] <= 0)
        | (data["devices"] <= 0)
        | (data["devices"] > data["tests"])
    )
    reasons["negative_performance"] = (
        (data["avg_d_kbps"] < 0)
        | (data["avg_u_kbps"] < 0)
        | (data["avg_lat_ms"] < 0)
        | (data["avg_lat_down_ms"] < 0).fillna(False)
        | (data["avg_lat_up_ms"] < 0).fillna(False)
    )
    reasons["invalid_period"] = (
        data["period_start"].isna()
        | ~data["quarter"].isin([1, 2, 3, 4])
        | (data["year"] < 2019)
    )
    reasons["invalid_region"] = data["adm1_name"].isna() | data["adm1_iso"].isna()

    exclude = reasons.any(axis=1)
    clean = data.loc[~exclude].copy()

    clean["avg_d_mbps"] = clean["avg_d_kbps"].astype("Float64") / 1000.0
    clean["avg_u_mbps"] = clean["avg_u_kbps"].astype("Float64") / 1000.0
    clean["quarter_label"] = clean["year"].astype(str) + "-Q" + clean["quarter"].astype(str)
    clean["measurement_volume"] = np.select(
        [
            clean["tests"] <= config.low_volume_max_tests,
            clean["tests"] <= config.medium_volume_max_tests,
        ],
        ["low", "medium"],
        default="high",
    )
    clean["loaded_latency_complete"] = (
        clean["avg_lat_down_ms"].notna() & clean["avg_lat_up_ms"].notna()
    )
    clean["quality_note"] = np.select(
        [
            (clean["measurement_volume"] == "low") & ~clean["loaded_latency_complete"],
            clean["measurement_volume"] == "low",
            ~clean["loaded_latency_complete"],
        ],
        ["low_volume;missing_loaded_latency", "low_volume", "missing_loaded_latency"],
        default="none",
    )
    clean = clean.sort_values(["period_start", "quadkey"]).reset_index(drop=True)

    audit = {
        "input_rows": input_rows,
        "output_rows": len(clean),
        "removed_rows": int(exclude.sum()),
        "removal_counts_by_reason": {
            column: int(reasons[column].sum()) for column in reasons.columns
        },
        "input_columns": input_columns,
        "output_columns": clean.columns.tolist(),
        "null_counts_before": nulls_before,
        "null_counts_after": {
            key: int(value) for key, value in clean.isna().sum().items()
        },
        "measurement_volume_thresholds": {
            "low": f"1-{config.low_volume_max_tests} tests",
            "medium": (
                f"{config.low_volume_max_tests + 1}-"
                f"{config.medium_volume_max_tests} tests"
            ),
            "high": f"{config.medium_volume_max_tests + 1}+ tests",
        },
        "measurement_volume_counts": {
            key: int(value)
            for key, value in clean["measurement_volume"].value_counts().sort_index().items()
        },
        "loaded_latency_complete_rows": int(clean["loaded_latency_complete"].sum()),
        "zero_idle_latency_rows_preserved": int((clean["avg_lat_ms"] == 0).sum()),
        "speed_conversion_rule": "Mbps = kbps / 1000",
        "sample_conversions": clean[
            ["quadkey", "avg_d_kbps", "avg_d_mbps", "avg_u_kbps", "avg_u_mbps"]
        ].head(5).to_dict(orient="records"),
        "grain": "one quadkey per quarter",
    }
    return clean, audit


def run_cleaning(input_path: Path, parquet_path: Path, csv_path: Path, audit_path: Path) -> dict:
    if not input_path.is_file():
        raise FileNotFoundError(f"Interim input not found: {input_path}")
    source = gpd.read_parquet(input_path)
    clean, audit = clean_frame(source)

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    clean.to_parquet(parquet_path, index=False)

    csv_frame = pd.DataFrame(clean.drop(columns="geometry"))
    csv_frame.insert(11, "centroid_wkt", clean.geometry.to_wkt())
    csv_frame.to_csv(csv_path, index=False, na_rep="")

    reopened = gpd.read_parquet(parquet_path)
    if len(reopened) != len(clean) or reopened["quadkey"].duplicated().any():
        raise ValueError("Written Parquet failed row-count or key validation.")
    csv_rows = sum(1 for _ in csv_path.open("r", encoding="utf-8")) - 1
    if csv_rows != len(clean):
        raise ValueError("Written CSV failed row-count validation.")

    audit.update(
        {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "input_path": input_path.resolve().as_posix(),
            "input_sha256": sha256_file(input_path),
            "parquet_path": parquet_path.resolve().as_posix(),
            "parquet_size_bytes": parquet_path.stat().st_size,
            "parquet_sha256": sha256_file(parquet_path),
            "csv_path": csv_path.resolve().as_posix(),
            "csv_size_bytes": csv_path.stat().st_size,
            "csv_sha256": sha256_file(csv_path),
        }
    )
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--parquet", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()
    result = run_cleaning(args.input, args.parquet, args.csv, args.audit)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
