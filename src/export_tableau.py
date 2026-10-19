"""Create a flat Tableau explorer export, audit, trace, preview, and KPI reconciliation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.export_power_bi import FACT_QUERY, calculate_kpis


DEFAULT_DATABASE = Path("data/processed/network_performance.sqlite")
DEFAULT_PRIORITY = Path("data/processed/investigation_priority_by_adm1.csv")
DEFAULT_EXPORT = Path("data/processed/tableau/TableauTileExplorer.csv")
DEFAULT_DICTIONARY = Path("data/processed/tableau/TableauFieldDictionary.csv")
DEFAULT_AUDIT = Path("reports/generated/tableau_export_audit.json")
DEFAULT_RECONCILIATION = Path("reports/generated/tableau_reconciliation.json")
DEFAULT_TRACE = Path("reports/generated/tableau_selected_tile_trace.json")
DEFAULT_PREVIEW = Path("reports/figures/tableau/geographic_explorer_build_reference.png")


FIELD_DICTIONARY = [
    ("quadkey", "Dimension", "String", "Map-tile identifier; combine with quarter for multi-period uniqueness."),
    ("period_start", "Dimension", "Date", "Quarter start date."),
    ("year", "Dimension", "Whole", "Calendar year derived from period start."),
    ("quarter", "Dimension", "Whole", "Calendar quarter number."),
    ("quarter_label", "Dimension", "String", "Human-readable quarter filter."),
    ("adm1_iso", "Dimension", "String", "Assigned ADM1 code."),
    ("adm1_name", "Dimension", "String", "Assigned ADM1 label."),
    ("longitude", "Dimension", "Geographic", "Tile centroid longitude; assign Longitude role."),
    ("latitude", "Dimension", "Geographic", "Tile centroid latitude; assign Latitude role."),
    ("avg_d_mbps", "Measure", "Decimal", "Mean tile download Mbps."),
    ("avg_u_mbps", "Measure", "Decimal", "Mean tile upload Mbps."),
    ("avg_lat_ms", "Measure", "Decimal", "Mean tile idle latency milliseconds."),
    ("avg_lat_down_ms", "Measure", "Decimal nullable", "Mean loaded download latency; missing is not zero."),
    ("avg_lat_up_ms", "Measure", "Decimal nullable", "Mean loaded upload latency; missing is not zero."),
    ("tests", "Measure", "Whole", "Contributing test count; not subscribers or population."),
    ("devices", "Measure", "Whole", "Tile-level unique devices; not globally deduplicated."),
    ("measurement_volume", "Dimension", "String", "Low 1-4, medium 5-19, high 20+ tests."),
    ("loaded_latency_complete", "Dimension", "Boolean", "Both loaded-latency metrics are present."),
    ("quality_note", "Dimension", "String", "Tile-level evidence warning."),
    ("boundary_ambiguous", "Dimension", "Boolean", "Centroid touched more than one ADM1 boundary before deterministic assignment."),
    ("base_score", "Measure", "Decimal", "Regional investigation-priority score, 0-100."),
    ("base_rank", "Measure", "Whole", "Regional comparative priority rank; 1 is highest."),
    ("priority_reason", "Dimension", "String", "Transparent regional score explanation."),
    ("data_quality_note", "Dimension", "String", "Regional scoring quality caveat."),
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _build_preview(frame: pd.DataFrame, selected: pd.Series, output_path: Path) -> None:
    regional = (
        frame.groupby("adm1_name", as_index=False)
        .apply(lambda group: pd.Series(calculate_kpis(group)), include_groups=False)
        .reset_index(drop=True)
        .sort_values("weighted_download_mbps")
    )
    fig = plt.figure(figsize=(16, 9), facecolor="#f6f8f7")
    grid = fig.add_gridspec(3, 12, height_ratios=[0.8, 4, 2.6], hspace=0.46, wspace=0.85)
    title = fig.add_subplot(grid[0, :]); title.axis("off")
    title.text(0, 0.72, "GEOGRAPHIC PERFORMANCE EXPLORER", fontsize=23, weight="bold", color="#173b35")
    title.text(0, 0.15, "TABLEAU BUILD REFERENCE - Q4 2024 - MEASUREMENT TILES, NOT COVERAGE", fontsize=10.5, color="#63736f")

    ax_map = fig.add_subplot(grid[1, :8])
    marks = ax_map.scatter(
        frame["longitude"], frame["latitude"], c=frame["avg_d_mbps"], s=6,
        cmap="viridis", alpha=0.65, vmin=frame["avg_d_mbps"].quantile(0.05),
        vmax=frame["avg_d_mbps"].quantile(0.95), linewidths=0,
    )
    ax_map.scatter([selected["longitude"]], [selected["latitude"]], s=85, facecolors="none", edgecolors="#d1495b", linewidths=2)
    ax_map.set(title="Tile download performance", xlabel="Longitude", ylabel="Latitude")
    fig.colorbar(marks, ax=ax_map, label="Download Mbps (color clipped p5-p95)")

    ax_bar = fig.add_subplot(grid[1, 8:])
    ax_bar.barh(regional["adm1_name"], regional["weighted_download_mbps"], color="#2a9d8f")
    ax_bar.set(title="Regional comparison", xlabel="Test-weighted download Mbps")
    ax_bar.grid(axis="x", alpha=0.2); ax_bar.set_axisbelow(True)

    ax_box = fig.add_subplot(grid[2, :8])
    order = regional["adm1_name"].tolist()
    values = [frame.loc[frame["adm1_name"] == region, "avg_lat_ms"] for region in order]
    ax_box.boxplot(values, tick_labels=order, showfliers=False)
    ax_box.tick_params(axis="x", rotation=25)
    ax_box.set(title="Idle-latency distribution by region", ylabel="Milliseconds")

    ax_detail = fig.add_subplot(grid[2, 8:]); ax_detail.axis("off")
    ax_detail.set_title("Selected tile details", loc="left", weight="bold")
    details = [
        ("Tile", str(selected["quadkey"])), ("Region", selected["adm1_name"]),
        ("Download", f"{selected['avg_d_mbps']:.3f} Mbps"),
        ("Upload", f"{selected['avg_u_mbps']:.3f} Mbps"),
        ("Idle latency", f"{selected['avg_lat_ms']:.0f} ms"),
        ("Tests / devices", f"{int(selected['tests'])} / {int(selected['devices'])}"),
        ("Volume", selected["measurement_volume"]),
    ]
    for index, (label, value) in enumerate(details):
        y = 0.88 - index * 0.12
        ax_detail.text(0, y, label.upper(), fontsize=8.5, color="#66756f", weight="bold")
        ax_detail.text(0.36, y, value, fontsize=10.5, color="#173b35")
    fig.text(0.01, 0.01, "Static build reference, not a Tableau screenshot. Selection ring identifies the documented real tile.", fontsize=9, color="#6b7280")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def export_tableau(
    database_path: Path,
    priority_path: Path,
    export_path: Path,
    dictionary_path: Path,
    audit_path: Path,
    reconciliation_path: Path,
    trace_path: Path,
    preview_path: Path,
) -> tuple[dict, dict, dict]:
    if not database_path.is_file() or not priority_path.is_file():
        raise FileNotFoundError("SQLite database and Phase 6 priority dataset are required.")
    with sqlite3.connect(database_path) as connection:
        fact = pd.read_sql_query(FACT_QUERY, connection)
        regions = pd.read_sql_query("SELECT adm1_iso, adm1_name FROM dim_region", connection)
    priority = pd.read_csv(priority_path)
    priority["quarter_label"] = "2024-Q4"
    frame = fact.merge(regions, on="adm1_iso", how="left", validate="many_to_one")
    score_columns = [
        "adm1_iso", "quarter_label", "base_score", "base_rank",
        "priority_reason", "data_quality_note",
    ]
    frame = frame.merge(priority[score_columns], on=["adm1_iso", "quarter_label"], how="left", validate="many_to_one")
    if frame[["adm1_name", "base_score", "base_rank"]].isna().any().any():
        raise ValueError("Tableau export contains unmatched geography or priority rows.")

    export_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(export_path, index=False, na_rep="")
    dictionary = pd.DataFrame(FIELD_DICTIONARY, columns=["field", "role", "type", "meaning_and_caution"])
    dictionary.to_csv(dictionary_path, index=False)

    selected = frame.sort_values(["tests", "quadkey"], ascending=[False, True]).iloc[0]
    region = frame[frame["adm1_iso"] == selected["adm1_iso"]]
    region_kpi = calculate_kpis(region)
    tile_numerator = float(selected["avg_d_mbps"] * selected["tests"])
    region_numerator = float((region["avg_d_mbps"] * region["tests"]).sum())
    trace = {
        "selection_rule": "highest test count, then ascending quadkey",
        "quadkey": str(selected["quadkey"]),
        "quarter_label": selected["quarter_label"],
        "adm1_iso": selected["adm1_iso"],
        "adm1_name": selected["adm1_name"],
        "longitude": float(selected["longitude"]),
        "latitude": float(selected["latitude"]),
        "avg_d_mbps": float(selected["avg_d_mbps"]),
        "avg_u_mbps": float(selected["avg_u_mbps"]),
        "avg_lat_ms": float(selected["avg_lat_ms"]),
        "tests": int(selected["tests"]),
        "devices": int(selected["devices"]),
        "measurement_volume": selected["measurement_volume"],
        "tile_download_numerator_mbps_tests": tile_numerator,
        "region_download_numerator_mbps_tests": region_numerator,
        "region_download_denominator_tests": region_kpi["tests"],
        "region_weighted_download_mbps": region_kpi["weighted_download_mbps"],
        "tile_share_of_region_download_numerator": tile_numerator / region_numerator,
        "base_priority_score": float(selected["base_score"]),
        "base_priority_rank": int(selected["base_rank"]),
        "interpretation": "A selected measurement tile contributing to an aggregate; not a tower or individual test.",
    }

    filters = {"all_bangladesh": None, "dhaka": "BD-C", "rajshani": "BD-E"}
    reconciliation = {"tolerance": 1e-9, "filters": {}}
    with sqlite3.connect(database_path) as connection:
        for label, iso in filters.items():
            subset = frame if iso is None else frame[frame["adm1_iso"] == iso]
            tableau = calculate_kpis(subset)
            where = "WHERE adm1_iso = ?" if iso else ""
            params = (iso,) if iso else ()
            sql = connection.execute(
                f"""SELECT COUNT(*), SUM(tests), SUM(devices),
                SUM(avg_d_mbps * tests) / (SUM(tests) * 1.0),
                SUM(avg_u_mbps * tests) / (SUM(tests) * 1.0),
                SUM(avg_lat_ms * tests) / (SUM(tests) * 1.0)
                FROM fact_tile_performance {where}""", params,
            ).fetchone()
            names = ["tiles", "tests", "devices", "weighted_download_mbps", "weighted_upload_mbps", "weighted_idle_latency_ms"]
            comparison = {}
            for metric, sqlite_value in zip(names, sql, strict=True):
                difference = abs(float(sqlite_value) - float(tableau[metric]))
                comparison[metric] = {
                    "sqlite": sqlite_value,
                    "tableau_export_recalculation": tableau[metric],
                    "absolute_difference": difference,
                    "pass": difference <= reconciliation["tolerance"],
                }
            reconciliation["filters"][label] = comparison
    reconciliation["all_pass"] = all(
        result["pass"] for group in reconciliation["filters"].values() for result in group.values()
    )

    _build_preview(frame, selected, preview_path)
    audit = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": database_path.as_posix(),
        "export": export_path.as_posix(),
        "rows": len(frame),
        "columns": len(frame.columns),
        "sha256": _sha256(export_path),
        "dictionary": dictionary_path.as_posix(),
        "dictionary_rows": len(dictionary),
        "preview": preview_path.as_posix(),
        "grain": "one measurement tile for one quarter, with repeated region-quarter priority attributes",
    }
    for path, payload in [(audit_path, audit), (reconciliation_path, reconciliation), (trace_path, trace)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return audit, reconciliation, trace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--priority", type=Path, default=DEFAULT_PRIORITY)
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT)
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--reconciliation", type=Path, default=DEFAULT_RECONCILIATION)
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    args = parser.parse_args()
    audit, reconciliation, trace = export_tableau(
        args.database, args.priority, args.export, args.dictionary, args.audit,
        args.reconciliation, args.trace, args.preview,
    )
    print(json.dumps({"audit": audit, "reconciliation": reconciliation, "trace": trace}, indent=2))


if __name__ == "__main__":
    main()
