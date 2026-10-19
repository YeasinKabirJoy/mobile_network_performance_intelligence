"""Create the audited Bangladesh Q4 2024 geographic subset.

The global Parquet source is scanned in batches with column projection and a
bounding-box predicate. Candidate tile centroids are then assigned to official
Bangladesh ADM1 polygons in EPSG:4326. The raw source is never modified.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


DEFAULT_SOURCE = Path("data/raw/2024-10-01_performance_mobile_tiles.parquet")
DEFAULT_BOUNDARY = Path("data/raw/geoBoundaries-BGD-ADM1.geojson")
DEFAULT_OUTPUT = Path("data/interim/bgd_mobile_tiles_2024_q4.parquet")
DEFAULT_AUDIT = Path("reports/generated/geographic_extraction_audit.json")
DEFAULT_FIGURE = Path("reports/figures/bgd_tile_centroids_2024_q4.png")

SOURCE_COLUMNS = [
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
]
BGD_BBOX = {"min_x": 88.0, "max_x": 92.8, "min_y": 20.5, "max_y": 26.7}


def _read_bbox_candidates(source: Path, batch_size: int = 250_000) -> tuple[pd.DataFrame, int]:
    """Project required columns and retain bbox candidates one batch at a time."""
    parquet_file = pq.ParquetFile(source)
    source_rows = parquet_file.metadata.num_rows
    frames: list[pd.DataFrame] = []

    for batch in parquet_file.iter_batches(columns=SOURCE_COLUMNS, batch_size=batch_size):
        x = batch.column(batch.schema.get_field_index("tile_x"))
        y = batch.column(batch.schema.get_field_index("tile_y"))
        mask = pc.and_(
            pc.and_(pc.greater_equal(x, BGD_BBOX["min_x"]), pc.less_equal(x, BGD_BBOX["max_x"])),
            pc.and_(pc.greater_equal(y, BGD_BBOX["min_y"]), pc.less_equal(y, BGD_BBOX["max_y"])),
        )
        filtered = pa.Table.from_batches([batch]).filter(mask)
        if filtered.num_rows:
            frames.append(filtered.to_pandas())

    if not frames:
        return pd.DataFrame(columns=SOURCE_COLUMNS), source_rows
    return pd.concat(frames, ignore_index=True), source_rows


def _assign_regions(candidates: pd.DataFrame, boundaries: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    """Assign centroid points to ADM1 polygons with deterministic boundary ties."""
    points = gpd.GeoDataFrame(
        candidates,
        geometry=gpd.points_from_xy(candidates["tile_x"], candidates["tile_y"]),
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(
        points,
        boundaries[["shapeName", "shapeISO", "geometry"]],
        how="inner",
        predicate="intersects",
    ).rename(columns={"shapeName": "adm1_name", "shapeISO": "adm1_iso"})

    match_counts = joined.groupby("quadkey").size()
    ambiguous_keys = set(match_counts[match_counts > 1].index)
    joined["boundary_ambiguous"] = joined["quadkey"].isin(ambiguous_keys)
    joined = (
        joined.sort_values(["quadkey", "adm1_iso"])
        .drop_duplicates("quadkey", keep="first")
        .drop(columns="index_right")
        .sort_values("quadkey")
        .reset_index(drop=True)
    )
    audit = {
        "ambiguous_boundary_centroids": len(ambiguous_keys),
        "unmatched_bbox_candidates": len(candidates) - len(joined),
    }
    return joined, audit


def _make_validation_plot(boundaries: gpd.GeoDataFrame, retained: gpd.GeoDataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 10))
    boundaries.plot(ax=ax, color="#eef3f7", edgecolor="#243746", linewidth=0.8)
    retained.plot(ax=ax, color="#087e8b", markersize=2.2, alpha=0.42)
    for _, row in boundaries.iterrows():
        label_point = row.geometry.representative_point()
        ax.text(label_point.x, label_point.y, row["shapeName"], fontsize=8, ha="center")
    ax.set_title("Q4 2024 Ookla mobile tile centroids retained for Bangladesh")
    ax.set_xlabel("Longitude (EPSG:4326)")
    ax.set_ylabel("Latitude (EPSG:4326)")
    ax.text(
        0,
        -0.09,
        "Centroid assignment; points are aggregated map tiles, not towers.\n"
        "Sources: Speedtest by Ookla open data and geoBoundaries ADM1.",
        transform=ax.transAxes,
        fontsize=8,
        va="top",
    )
    ax.grid(color="#cad3da", linewidth=0.4, alpha=0.7)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def extract(source: Path, boundary: Path, output: Path, audit_path: Path, figure_path: Path) -> dict:
    """Execute and validate the Phase 2 extraction."""
    if not source.is_file() or not boundary.is_file():
        raise FileNotFoundError("The verified Phase 1 source and boundary files are required.")

    boundaries = gpd.read_file(boundary)
    if boundaries.crs is None:
        raise ValueError("Boundary CRS is missing.")
    boundaries = boundaries.to_crs("EPSG:4326")
    invalid_boundaries = int((~boundaries.geometry.is_valid).sum())
    empty_boundaries = int(boundaries.geometry.is_empty.sum())
    if invalid_boundaries or empty_boundaries:
        raise ValueError(
            f"Boundary validation failed: {invalid_boundaries} invalid, {empty_boundaries} empty."
        )

    candidates, source_rows = _read_bbox_candidates(source)
    if candidates.empty:
        raise ValueError("Bounding-box filter returned no candidate tiles.")
    retained, spatial_audit = _assign_regions(candidates, boundaries)
    if retained.empty:
        raise ValueError("Precise spatial selection returned no Bangladesh tiles.")

    duplicate_quadkeys = int(retained["quadkey"].duplicated().sum())
    missing_geometry = int(retained.geometry.isna().sum() + retained.geometry.is_empty.sum())
    regions_expected = sorted(boundaries["shapeISO"].dropna().unique().tolist())
    regions_observed = sorted(retained["adm1_iso"].dropna().unique().tolist())
    if duplicate_quadkeys or missing_geometry or regions_observed != regions_expected:
        raise ValueError(
            "Extraction validation failed: duplicate keys, geometry errors, or missing ADM1 coverage."
        )

    retained["period_start"] = pd.Timestamp("2024-10-01")
    retained["year"] = 2024
    retained["quarter"] = 4
    retained["source_layer"] = "performance_mobile_tiles"

    output.parent.mkdir(parents=True, exist_ok=True)
    retained.to_parquet(output, index=False)
    _make_validation_plot(boundaries, retained, figure_path)

    audit = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "assignment_rule": "bbox pre-filter, then EPSG:4326 centroid intersects ADM1; ties use ascending shapeISO",
        "source_rows": source_rows,
        "projected_source_columns": SOURCE_COLUMNS,
        "bbox": BGD_BBOX,
        "bbox_candidate_rows": len(candidates),
        "retained_rows": len(retained),
        **spatial_audit,
        "duplicate_retained_quadkeys": duplicate_quadkeys,
        "missing_retained_geometry": missing_geometry,
        "boundary_crs": boundaries.crs.to_string(),
        "boundary_features": len(boundaries),
        "invalid_boundary_geometries": invalid_boundaries,
        "empty_boundary_geometries": empty_boundaries,
        "regions_expected": regions_expected,
        "regions_observed": regions_observed,
        "rows_by_adm1": {
            key: int(value)
            for key, value in retained.groupby("adm1_name").size().sort_index().items()
        },
        "tests_by_adm1": {
            key: int(value)
            for key, value in retained.groupby("adm1_name")["tests"].sum().sort_index().items()
        },
        "devices_by_adm1": {
            key: int(value)
            for key, value in retained.groupby("adm1_name")["devices"].sum().sort_index().items()
        },
        "retained_coordinate_extent": {
            "min_x": float(retained["tile_x"].min()),
            "max_x": float(retained["tile_x"].max()),
            "min_y": float(retained["tile_y"].min()),
            "max_y": float(retained["tile_y"].max()),
        },
        "output_path": output.resolve().as_posix(),
        "output_size_bytes": output.stat().st_size,
        "figure_path": figure_path.resolve().as_posix(),
        "limitations": [
            "Centroid assignment does not measure tile-polygon overlap.",
            "Unmatched bbox candidates mostly represent neighboring countries or water.",
            "Administrative labels are retained from the selected boundary release.",
        ],
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()
    result = extract(args.source, args.boundary, args.output, args.audit, args.figure)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
