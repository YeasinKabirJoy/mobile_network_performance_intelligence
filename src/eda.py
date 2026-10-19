"""Produce Phase 5 descriptive statistics, figures, and grounded evidence."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image, ImageOps, ImageDraw


DEFAULT_INPUT = Path("data/processed/bgd_mobile_tiles_2024_q4_clean.parquet")
DEFAULT_BOUNDARY = Path("data/raw/geoBoundaries-BGD-ADM1.geojson")
DEFAULT_OUTPUT_DIR = Path("reports/figures/eda")
DEFAULT_SUMMARY = Path("reports/generated/eda_summary.json")

PALETTE = {"low": "#9aa5b1", "medium": "#087e8b", "high": "#f28e2b"}


def _metric_summary(series: pd.Series) -> dict[str, float]:
    return {
        "count": int(series.count()),
        "mean": float(series.mean()),
        "median": float(series.median()),
        "std": float(series.std()),
        "p05": float(series.quantile(0.05)),
        "p25": float(series.quantile(0.25)),
        "p75": float(series.quantile(0.75)),
        "p95": float(series.quantile(0.95)),
        "p99": float(series.quantile(0.99)),
        "min": float(series.min()),
        "max": float(series.max()),
        "skew": float(series.skew()),
    }


def compute_summary(frame: gpd.GeoDataFrame) -> dict:
    tests = frame["tests"].astype(float)
    regional_rows = []
    for region, group in frame.groupby("adm1_name"):
        weights = group["tests"].astype(float)
        regional_rows.append(
            {
                "adm1_name": region,
                "tiles": len(group),
                "tests": int(group["tests"].sum()),
                "devices": int(group["devices"].sum()),
                "median_download_mbps": float(group["avg_d_mbps"].median()),
                "weighted_download_mbps": float((group["avg_d_mbps"] * weights).sum() / weights.sum()),
                "weighted_upload_mbps": float((group["avg_u_mbps"] * weights).sum() / weights.sum()),
                "weighted_idle_latency_ms": float((group["avg_lat_ms"] * weights).sum() / weights.sum()),
            }
        )
    return {
        "rows": len(frame),
        "tests": int(frame["tests"].sum()),
        "devices": int(frame["devices"].sum()),
        "metrics": {
            name: _metric_summary(frame[name])
            for name in ["avg_d_mbps", "avg_u_mbps", "avg_lat_ms", "tests", "devices"]
        },
        "correlations": {
            "pearson_download_latency": float(frame["avg_d_mbps"].corr(frame["avg_lat_ms"])),
            "spearman_download_latency": float(
                frame["avg_d_mbps"].rank().corr(frame["avg_lat_ms"].rank())
            ),
            "pearson_tests_download": float(tests.corr(frame["avg_d_mbps"])),
            "spearman_tests_download": float(tests.rank().corr(frame["avg_d_mbps"].rank())),
        },
        "counts": {
            "download_below_10_mbps": int((frame["avg_d_mbps"] < 10).sum()),
            "idle_latency_above_100_ms": int((frame["avg_lat_ms"] > 100).sum()),
            "loaded_latency_incomplete": int((~frame["loaded_latency_complete"]).sum()),
        },
        "measurement_volume": {
            key: int(value)
            for key, value in frame["measurement_volume"].value_counts().sort_index().items()
        },
        "regional": sorted(regional_rows, key=lambda row: row["adm1_name"]),
        "weighted_national": {
            "download_mbps": float((frame["avg_d_mbps"] * tests).sum() / tests.sum()),
            "upload_mbps": float((frame["avg_u_mbps"] * tests).sum() / tests.sum()),
            "idle_latency_ms": float((frame["avg_lat_ms"] * tests).sum() / tests.sum()),
        },
    }


def _save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def create_figures(frame: gpd.GeoDataFrame, boundaries: gpd.GeoDataFrame, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    outputs: list[Path] = []

    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.histplot(frame["avg_d_mbps"], bins=70, color="#087e8b", ax=ax)
    ax.axvline(frame["avg_d_mbps"].median(), color="#d1495b", linestyle="--", label="Median")
    ax.axvline(frame["avg_d_mbps"].mean(), color="#f28e2b", linestyle=":", label="Mean")
    ax.set(title="Distribution of tile-average download speed", xlabel="Download (Mbps)", ylabel="Tiles")
    ax.legend()
    path = output_dir / "01_download_distribution.png"; _save(fig, path); outputs.append(path)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.histplot(frame["avg_u_mbps"], bins=70, color="#4e79a7", ax=ax)
    ax.axvline(frame["avg_u_mbps"].median(), color="#d1495b", linestyle="--", label="Median")
    ax.axvline(frame["avg_u_mbps"].mean(), color="#f28e2b", linestyle=":", label="Mean")
    ax.set(title="Distribution of tile-average upload speed", xlabel="Upload (Mbps)", ylabel="Tiles")
    ax.legend()
    path = output_dir / "02_upload_distribution.png"; _save(fig, path); outputs.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.histplot(frame["avg_lat_ms"], bins=80, color="#e15759", ax=axes[0])
    axes[0].set(title="Full idle-latency distribution", xlabel="Idle latency (ms)", ylabel="Tiles")
    p99 = frame["avg_lat_ms"].quantile(0.99)
    sns.histplot(frame.loc[frame["avg_lat_ms"] <= p99, "avg_lat_ms"], bins=50, color="#e15759", ax=axes[1])
    axes[1].axvline(frame["avg_lat_ms"].median(), color="#243746", linestyle="--", label="Median")
    axes[1].set(title="Idle latency through the 99th percentile", xlabel="Idle latency (ms)", ylabel="Tiles")
    axes[1].legend()
    path = output_dir / "03_idle_latency_distribution.png"; _save(fig, path); outputs.append(path)

    order = frame.groupby("adm1_name")["avg_d_mbps"].median().sort_values().index
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=frame, x="avg_d_mbps", y="adm1_name", order=order, showfliers=False, color="#76b7b2", ax=ax)
    ax.set(title="Tile download distributions by ADM1", xlabel="Download (Mbps), outliers hidden for scale", ylabel="ADM1")
    path = output_dir / "04_regional_download_boxplot.png"; _save(fig, path); outputs.append(path)

    regional = pd.DataFrame(compute_summary(frame)["regional"]).sort_values("weighted_download_mbps")
    fig, ax = plt.subplots(figsize=(10, 6))
    positions = np.arange(len(regional))
    ax.barh(positions - 0.18, regional["weighted_download_mbps"], height=0.36, label="Download", color="#087e8b")
    ax.barh(positions + 0.18, regional["weighted_upload_mbps"], height=0.36, label="Upload", color="#f28e2b")
    ax.set_yticks(positions, regional["adm1_name"])
    ax.set(title="Test-weighted throughput by ADM1", xlabel="Mbps", ylabel="ADM1")
    ax.legend()
    path = output_dir / "05_regional_weighted_throughput.png"; _save(fig, path); outputs.append(path)

    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(
        data=frame, x="avg_d_mbps", y="avg_lat_ms", hue="measurement_volume",
        hue_order=["low", "medium", "high"], palette=PALETTE, alpha=0.45,
        s=20, linewidth=0, ax=ax,
    )
    ax.set_yscale("symlog", linthresh=10)
    ax.set_ylim(bottom=0)
    ax.set(title="Download speed and idle latency by evidence volume", xlabel="Download (Mbps)", ylabel="Idle latency (ms, symlog scale)")
    path = output_dir / "06_download_latency_scatter.png"; _save(fig, path); outputs.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.histplot(frame["tests"], bins=60, color="#59a14f", ax=axes[0])
    axes[0].set_yscale("log")
    axes[0].set(title="Tests per tile", xlabel="Tests", ylabel="Tiles (log scale)")
    volume_counts = frame["measurement_volume"].value_counts().reindex(["low", "medium", "high"])
    axes[1].bar(volume_counts.index, volume_counts.values, color=[PALETTE[k] for k in volume_counts.index])
    axes[1].set(title="Tiles by measurement-volume category", xlabel="Category", ylabel="Tiles")
    path = output_dir / "07_measurement_volume.png"; _save(fig, path); outputs.append(path)

    boundaries = boundaries.to_crs(frame.crs)
    fig, ax = plt.subplots(figsize=(9, 10))
    boundaries.plot(ax=ax, color="#edf2f4", edgecolor="#243746", linewidth=0.7)
    cap = frame["avg_d_mbps"].quantile(0.95)
    clipped = frame.assign(map_download_mbps=frame["avg_d_mbps"].clip(upper=cap))
    clipped.plot(
        ax=ax, column="map_download_mbps", cmap="viridis", markersize=3,
        alpha=0.7, legend=True,
        legend_kwds={"label": f"Download Mbps (color capped at p95 = {cap:.1f})"},
    )
    ax.set(title="Geographic distribution of tile-average download speed", xlabel="Longitude", ylabel="Latitude")
    path = output_dir / "08_download_map.png"; _save(fig, path); outputs.append(path)
    return outputs


def create_contact_sheet(paths: list[Path], output: Path) -> None:
    thumbs = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((700, 450))
        canvas = Image.new("RGB", (720, 490), "white")
        canvas.paste(image, ((720 - image.width) // 2, 25))
        ImageDraw.Draw(canvas).text((12, 8), path.name, fill="black")
        thumbs.append(canvas)
    sheet = Image.new("RGB", (1440, 490 * 4), "white")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % 2) * 720, (index // 2) * 490))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def run_eda(input_path: Path, boundary_path: Path, output_dir: Path, summary_path: Path) -> dict:
    frame = gpd.read_parquet(input_path)
    boundaries = gpd.read_file(boundary_path)
    summary = compute_summary(frame)
    figures = create_figures(frame, boundaries, output_dir)
    contact_sheet = output_dir / "eda_contact_sheet.jpg"
    create_contact_sheet(figures, contact_sheet)
    summary.update(
        {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "figure_count": len(figures),
            "figures": [path.as_posix() for path in figures],
            "contact_sheet": contact_sheet.as_posix(),
            "scope": "Descriptive Q4 2024 tile-level and test-weighted summaries for retained Bangladesh observations",
        }
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()
    result = run_eda(args.input, args.boundary, args.output_dir, args.summary)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
