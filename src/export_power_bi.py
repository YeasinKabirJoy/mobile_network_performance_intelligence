"""Create curated Power BI imports and reconcile their core measures to SQLite."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_DATABASE = Path("data/processed/network_performance.sqlite")
DEFAULT_PRIORITY = Path("data/processed/investigation_priority_by_adm1.csv")
DEFAULT_OUTPUT_DIR = Path("data/processed/power_bi")
DEFAULT_AUDIT = Path("reports/generated/power_bi_export_audit.json")
DEFAULT_RECONCILIATION = Path("reports/generated/power_bi_reconciliation.json")
DEFAULT_PREVIEW = Path("reports/figures/power_bi/management_dashboard_build_reference.png")


FACT_QUERY = """
SELECT
    quadkey, period_start, year, quarter, quarter_label, adm1_iso,
    longitude, latitude, avg_d_mbps, avg_u_mbps,
    avg_lat_ms, avg_lat_down_ms, avg_lat_up_ms,
    tests, devices, measurement_volume, loaded_latency_complete,
    quality_note, boundary_ambiguous
FROM fact_tile_performance
ORDER BY period_start, adm1_iso, quadkey
"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def calculate_kpis(frame: pd.DataFrame) -> dict[str, float | int]:
    tests = float(frame["tests"].sum())
    latency = frame["avg_lat_ms"].notna()
    latency_tests = float(frame.loc[latency, "tests"].sum())
    return {
        "tiles": int(len(frame)),
        "tests": int(tests),
        "devices": int(frame["devices"].sum()),
        "weighted_download_mbps": float((frame["avg_d_mbps"] * frame["tests"]).sum() / tests),
        "weighted_upload_mbps": float((frame["avg_u_mbps"] * frame["tests"]).sum() / tests),
        "weighted_idle_latency_ms": float(
            (frame.loc[latency, "avg_lat_ms"] * frame.loc[latency, "tests"]).sum() / latency_tests
        ),
    }


def _sql_kpis(connection: sqlite3.Connection, adm1_iso: str | None) -> dict[str, float | int]:
    where = "WHERE adm1_iso = ?" if adm1_iso else ""
    parameters = (adm1_iso,) if adm1_iso else ()
    row = connection.execute(
        f"""
        SELECT COUNT(*), SUM(tests), SUM(devices),
               SUM(avg_d_mbps * tests) / NULLIF(SUM(tests) * 1.0, 0),
               SUM(avg_u_mbps * tests) / NULLIF(SUM(tests) * 1.0, 0),
               SUM(CASE WHEN avg_lat_ms IS NOT NULL THEN avg_lat_ms * tests END) /
                   NULLIF(SUM(CASE WHEN avg_lat_ms IS NOT NULL THEN tests END) * 1.0, 0)
        FROM fact_tile_performance {where}
        """,
        parameters,
    ).fetchone()
    names = [
        "tiles", "tests", "devices", "weighted_download_mbps",
        "weighted_upload_mbps", "weighted_idle_latency_ms",
    ]
    return dict(zip(names, row, strict=True))


def _build_preview(fact: pd.DataFrame, priority: pd.DataFrame, output_path: Path) -> None:
    overall = calculate_kpis(fact)
    regional = (
        fact.groupby("adm1_name", as_index=False)
        .apply(lambda group: pd.Series(calculate_kpis(group)), include_groups=False)
        .reset_index(drop=True)
        .sort_values("weighted_download_mbps")
    )
    ordered_priority = priority.sort_values("base_rank")

    fig = plt.figure(figsize=(16, 9), facecolor="#f4f7fb")
    grid = fig.add_gridspec(3, 12, height_ratios=[0.7, 1.1, 4.2], hspace=0.35, wspace=0.75)
    title = fig.add_subplot(grid[0, :]); title.axis("off")
    title.text(0, 0.7, "MOBILE NETWORK PERFORMANCE", fontsize=24, weight="bold", color="#17324d")
    title.text(0, 0.18, "POWER BI BUILD REFERENCE - Q4 2024 - BANGLADESH", fontsize=11, color="#5d6b78")

    cards = [
        ("TILES", f"{overall['tiles']:,}"), ("TESTS", f"{overall['tests']:,}"),
        ("DEVICES*", f"{overall['devices']:,}"),
        ("DOWNLOAD", f"{overall['weighted_download_mbps']:.2f} Mbps"),
        ("UPLOAD", f"{overall['weighted_upload_mbps']:.2f} Mbps"),
        ("IDLE LATENCY", f"{overall['weighted_idle_latency_ms']:.2f} ms"),
    ]
    starts = [0, 2, 4, 6, 8, 10]
    widths = [2, 2, 2, 2, 2, 2]
    for (label, value), start, width in zip(cards, starts, widths, strict=True):
        ax = fig.add_subplot(grid[1, start:start + width])
        ax.set_facecolor("white"); ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_color("#d9e2ec")
        ax.text(0.06, 0.72, label, transform=ax.transAxes, fontsize=9, color="#637381", weight="bold")
        ax.text(0.06, 0.25, value, transform=ax.transAxes, fontsize=17, color="#17324d", weight="bold")

    ax1 = fig.add_subplot(grid[2, :7])
    ax1.barh(regional["adm1_name"], regional["weighted_download_mbps"], color="#2f80ed")
    ax1.set_title("Test-weighted download by region", loc="left", weight="bold")
    ax1.set_xlabel("Mbps"); ax1.grid(axis="x", alpha=0.25); ax1.set_axisbelow(True)

    ax2 = fig.add_subplot(grid[2, 7:])
    shown = ordered_priority.sort_values("base_score")
    ax2.barh(shown["adm1_name"], shown["base_score"], color="#d1495b")
    ax2.set_title("Investigation priority", loc="left", weight="bold")
    ax2.set_xlabel("Score (0-100)"); ax2.grid(axis="x", alpha=0.25); ax2.set_axisbelow(True)
    fig.text(0.01, 0.01, "* Summed tile device counts. Static build reference, not a Power BI screenshot. Public tile aggregates do not prove coverage or faults.", fontsize=9, color="#6b7280")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def export_power_bi(
    database_path: Path,
    priority_path: Path,
    output_dir: Path,
    audit_path: Path,
    reconciliation_path: Path,
    preview_path: Path,
) -> tuple[dict, dict]:
    if not database_path.is_file() or not priority_path.is_file():
        raise FileNotFoundError("SQLite database and Phase 6 priority dataset are required.")
    output_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        fact = pd.read_sql_query(FACT_QUERY, connection)
        regions = pd.read_sql_query(
            "SELECT adm1_iso, adm1_name FROM dim_region ORDER BY adm1_iso", connection
        )
        sql_results = {
            "all_bangladesh": _sql_kpis(connection, None),
            "dhaka": _sql_kpis(connection, "BD-C"),
            "rajshani": _sql_kpis(connection, "BD-E"),
        }

    priority = pd.read_csv(priority_path)
    priority["quarter_label"] = "2024-Q4"
    regions["country"] = "Bangladesh"
    quarters = fact[["quarter_label", "period_start", "year", "quarter"]].drop_duplicates()
    fact = fact.merge(regions[["adm1_iso", "adm1_name"]], on="adm1_iso", how="left", validate="many_to_one")

    exports = {
        "FactTilePerformance.csv": fact,
        "DimRegion.csv": regions,
        "DimQuarter.csv": quarters,
        "FactRegionPriority.csv": priority,
    }
    files = []
    for name, frame in exports.items():
        path = output_dir / name
        frame.to_csv(path, index=False, na_rep="")
        files.append({"path": path.as_posix(), "rows": len(frame), "sha256": _sha256(path)})

    export_results = {
        "all_bangladesh": calculate_kpis(fact),
        "dhaka": calculate_kpis(fact[fact["adm1_iso"] == "BD-C"]),
        "rajshani": calculate_kpis(fact[fact["adm1_iso"] == "BD-E"]),
    }
    reconciliation = {"filters": {}, "tolerance": 1e-9}
    for label in sql_results:
        comparisons = {}
        for metric, sql_value in sql_results[label].items():
            export_value = export_results[label][metric]
            difference = abs(float(sql_value) - float(export_value))
            comparisons[metric] = {
                "sqlite": sql_value,
                "power_bi_import_recalculation": export_value,
                "absolute_difference": difference,
                "pass": difference <= reconciliation["tolerance"],
            }
        reconciliation["filters"][label] = comparisons
    reconciliation["all_pass"] = all(
        item["pass"]
        for filtered in reconciliation["filters"].values()
        for item in filtered.values()
    )

    _build_preview(fact, priority, preview_path)
    audit = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": database_path.as_posix(),
        "storage_mode": "Power BI Import from curated CSV files",
        "files": files,
        "relationships": [
            "DimRegion[adm1_iso] 1:* FactTilePerformance[adm1_iso]",
            "DimRegion[adm1_iso] 1:* FactRegionPriority[adm1_iso]",
            "DimQuarter[quarter_label] 1:* FactTilePerformance[quarter_label]",
            "DimQuarter[quarter_label] 1:* FactRegionPriority[quarter_label]",
        ],
        "preview": preview_path.as_posix(),
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    reconciliation_path.write_text(json.dumps(reconciliation, indent=2), encoding="utf-8")
    return audit, reconciliation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--priority", type=Path, default=DEFAULT_PRIORITY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--reconciliation", type=Path, default=DEFAULT_RECONCILIATION)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    args = parser.parse_args()
    audit, reconciliation = export_power_bi(
        args.database, args.priority, args.output_dir, args.audit, args.reconciliation, args.preview
    )
    print(json.dumps({"audit": audit, "reconciliation": reconciliation}, indent=2))


if __name__ == "__main__":
    main()
