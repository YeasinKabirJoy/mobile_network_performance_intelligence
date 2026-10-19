"""Validate the processed Phase 3 dataset and emit machine-readable results."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

from src.config import CLEANING


DEFAULT_INPUT = Path("data/processed/bgd_mobile_tiles_2024_q4_clean.parquet")
DEFAULT_OUTPUT = Path("reports/generated/processed_validation.json")


def validate_processed(frame: gpd.GeoDataFrame) -> dict:
    required = {
        "quadkey", "period_start", "adm1_name", "adm1_iso", "avg_d_kbps",
        "avg_d_mbps", "avg_u_kbps", "avg_u_mbps", "tests", "devices",
        "measurement_volume", "loaded_latency_complete", "quality_note", "geometry",
    }
    checks = {
        "nonempty": len(frame) > 0,
        "required_columns_present": required.issubset(frame.columns),
        "crs_is_epsg_4326": frame.crs is not None and frame.crs.to_epsg() == 4326,
        "tile_period_key_unique": not frame.duplicated(["quadkey", "period_start"]).any(),
        "required_values_nonnull": not frame[
            ["quadkey", "period_start", "adm1_name", "adm1_iso", "tests", "devices"]
        ].isna().any().any(),
        "counts_consistent": bool(
            ((frame["tests"] > 0) & (frame["devices"] > 0) & (frame["tests"] >= frame["devices"])).all()
        ),
        "download_conversion_exact": bool(
            ((frame["avg_d_kbps"] / 1000 - frame["avg_d_mbps"]).abs() < 1e-12).all()
        ),
        "upload_conversion_exact": bool(
            ((frame["avg_u_kbps"] / 1000 - frame["avg_u_mbps"]).abs() < 1e-12).all()
        ),
        "measurement_volume_valid": bool(
            frame["measurement_volume"].isin(["low", "medium", "high"]).all()
        ),
        "geometry_complete": bool(frame.geometry.notna().all() and (~frame.geometry.is_empty).all()),
        "all_eight_adm1_present": frame["adm1_iso"].nunique() == 8,
    }
    expected_volume = frame["tests"].map(
        lambda count: "low"
        if count <= CLEANING.low_volume_max_tests
        else "medium"
        if count <= CLEANING.medium_volume_max_tests
        else "high"
    )
    checks["measurement_volume_matches_tests"] = bool(
        (expected_volume == frame["measurement_volume"]).all()
    )
    checks["loaded_latency_flag_correct"] = bool(
        (
            frame["loaded_latency_complete"]
            == (frame["avg_lat_down_ms"].notna() & frame["avg_lat_up_ms"].notna())
        ).all()
    )
    return {
        "row_count": len(frame),
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    frame = gpd.read_parquet(args.input)
    result = validate_processed(frame)
    result["validated_at_utc"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
