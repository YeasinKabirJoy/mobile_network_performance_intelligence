"""Build an explainable ADM1 investigation-priority score and sensitivity analysis."""

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


DEFAULT_INPUT = Path("data/processed/bgd_mobile_tiles_2024_q4_clean.parquet")
DEFAULT_CSV = Path("data/processed/investigation_priority_by_adm1.csv")
DEFAULT_PARQUET = Path("data/processed/investigation_priority_by_adm1.parquet")
DEFAULT_AUDIT = Path("reports/generated/scoring_audit.json")
DEFAULT_FIGURE_DIR = Path("reports/figures/scoring")

SCENARIOS = {
    "base": {"speed": 0.45, "latency": 0.35, "sufficiency": 0.20, "persistence": 0.0},
    "speed_emphasis": {"speed": 0.60, "latency": 0.25, "sufficiency": 0.15, "persistence": 0.0},
    "latency_emphasis": {"speed": 0.30, "latency": 0.55, "sufficiency": 0.15, "persistence": 0.0},
    "lower_volume_influence": {"speed": 0.50, "latency": 0.40, "sufficiency": 0.10, "persistence": 0.0},
}


def _percentile(series: pd.Series, higher_is_higher: bool = True) -> pd.Series:
    """Return deterministic 0-1 rank percentiles with both extremes represented."""
    if len(series) == 1:
        return pd.Series(0.5, index=series.index)
    ranks = series.rank(method="average", ascending=True)
    result = (ranks - 1) / (len(series) - 1)
    return result if higher_is_higher else 1 - result


def aggregate_regions(frame: gpd.GeoDataFrame) -> pd.DataFrame:
    rows = []
    for (adm1_iso, adm1_name), group in frame.groupby(["adm1_iso", "adm1_name"]):
        tests = group["tests"].astype(float)
        rows.append(
            {
                "adm1_iso": adm1_iso,
                "adm1_name": adm1_name,
                "tiles": len(group),
                "tests": int(group["tests"].sum()),
                "devices": int(group["devices"].sum()),
                "weighted_download_mbps": float((group["avg_d_mbps"] * tests).sum() / tests.sum()),
                "weighted_upload_mbps": float((group["avg_u_mbps"] * tests).sum() / tests.sum()),
                "weighted_idle_latency_ms": float((group["avg_lat_ms"] * tests).sum() / tests.sum()),
                "low_volume_tile_share": float((group["measurement_volume"] == "low").mean()),
                "high_volume_tile_share": float((group["measurement_volume"] == "high").mean()),
                "loaded_latency_incomplete_share": float((~group["loaded_latency_complete"]).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("adm1_iso").reset_index(drop=True)


def add_components(regions: pd.DataFrame) -> pd.DataFrame:
    required = [
        "weighted_download_mbps",
        "weighted_upload_mbps",
        "weighted_idle_latency_ms",
        "tests",
        "high_volume_tile_share",
    ]
    missing_columns = [column for column in required if column not in regions]
    if missing_columns:
        raise ValueError(f"Missing required scoring columns: {missing_columns}")
    missing_values = regions[required].isna().any()
    if missing_values.any():
        raise ValueError(
            "Required scoring inputs contain missing values: "
            f"{missing_values[missing_values].index.tolist()}"
        )
    result = regions.copy()
    result["download_weakness"] = _percentile(result["weighted_download_mbps"], higher_is_higher=False)
    result["upload_weakness"] = _percentile(result["weighted_upload_mbps"], higher_is_higher=False)
    result["speed_weakness"] = (result["download_weakness"] + result["upload_weakness"]) / 2
    result["latency_weakness"] = _percentile(result["weighted_idle_latency_ms"], higher_is_higher=True)
    result["test_sufficiency"] = _percentile(np.log1p(result["tests"]), higher_is_higher=True)
    result["high_volume_sufficiency"] = _percentile(result["high_volume_tile_share"], higher_is_higher=True)
    result["data_sufficiency"] = (result["test_sufficiency"] + result["high_volume_sufficiency"]) / 2
    result["persistence_component"] = np.nan
    return result


def score_scenarios(regions: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    scored = add_components(regions)
    scenario_results: dict[str, pd.DataFrame] = {}
    for name, weights in SCENARIOS.items():
        scenario = scored[["adm1_iso", "adm1_name"]].copy()
        scenario["score"] = 100 * (
            weights["speed"] * scored["speed_weakness"]
            + weights["latency"] * scored["latency_weakness"]
            + weights["sufficiency"] * scored["data_sufficiency"]
        )
        scenario["rank"] = scenario["score"].rank(method="min", ascending=False).astype(int)
        scenario = scenario.sort_values(["rank", "adm1_iso"]).reset_index(drop=True)
        scenario_results[name] = scenario
        scored[f"{name}_score"] = scored["adm1_iso"].map(scenario.set_index("adm1_iso")["score"])
        scored[f"{name}_rank"] = scored["adm1_iso"].map(scenario.set_index("adm1_iso")["rank"])

    scored["priority_reason"] = scored.apply(_reason, axis=1)
    scored["data_quality_note"] = scored.apply(
        lambda row: (
            f"{row['low_volume_tile_share']:.1%} low-volume tiles; "
            f"{row['loaded_latency_incomplete_share']:.1%} incomplete loaded latency; "
            "single-quarter persistence unavailable"
        ),
        axis=1,
    )
    scored = scored.sort_values(["base_rank", "adm1_iso"]).reset_index(drop=True)
    return scored, scenario_results


def _reason(row: pd.Series) -> str:
    factors = [
        (row["speed_weakness"], "comparatively weak speed"),
        (row["latency_weakness"], "comparatively high idle latency"),
        (row["data_sufficiency"], "stronger evidence volume"),
    ]
    factors.sort(reverse=True)
    return "; ".join(label for _, label in factors[:2])


def _figures(scored: pd.DataFrame, scenarios: dict[str, pd.DataFrame], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    outputs = []

    ordered = scored.sort_values("base_score")
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(ordered["adm1_name"], ordered["base_score"], color="#d1495b")
    ax.bar_label(bars, fmt="%.1f", padding=3)
    ax.set(xlabel="Priority score (0-100)", ylabel="ADM1", title="Explainable investigation priority - base weights")
    ax.text(
        0, -0.13,
        "45% speed weakness + 35% latency weakness + 20% data sufficiency; not fault probability.",
        transform=ax.transAxes, fontsize=9,
    )
    fig.tight_layout(); path = output_dir / "01_priority_score.png"; fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig); outputs.append(path)

    ranks = pd.DataFrame(
        {name: result.set_index("adm1_name")["rank"] for name, result in scenarios.items()}
    ).loc[scored.sort_values("base_rank")["adm1_name"]]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(ranks, annot=True, fmt="d", cmap="YlOrRd_r", cbar_kws={"label": "Rank (1 = highest priority)"}, ax=ax)
    ax.set(title="Priority-rank sensitivity to alternative weights", xlabel="Scenario", ylabel="ADM1")
    fig.tight_layout(); path = output_dir / "02_rank_sensitivity.png"; fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig); outputs.append(path)
    return outputs


def run_scoring(input_path: Path, csv_path: Path, parquet_path: Path, audit_path: Path, figure_dir: Path) -> dict:
    frame = gpd.read_parquet(input_path)
    regions = aggregate_regions(frame)
    scored, scenarios = score_scenarios(regions)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(csv_path, index=False, na_rep="")
    scored.to_parquet(parquet_path, index=False)
    figures = _figures(scored, scenarios, figure_dir)

    traces = []
    for _, row in scored.head(3).iterrows():
        traces.append(
            {
                "adm1_iso": row["adm1_iso"],
                "adm1_name": row["adm1_name"],
                "inputs": {
                    "weighted_download_mbps": row["weighted_download_mbps"],
                    "weighted_upload_mbps": row["weighted_upload_mbps"],
                    "weighted_idle_latency_ms": row["weighted_idle_latency_ms"],
                    "tests": int(row["tests"]),
                    "high_volume_tile_share": row["high_volume_tile_share"],
                },
                "components": {
                    "speed_weakness": row["speed_weakness"],
                    "latency_weakness": row["latency_weakness"],
                    "data_sufficiency": row["data_sufficiency"],
                    "persistence": None,
                },
                "base_formula": (
                    f"100 * (0.45 * {row['speed_weakness']:.6f} + "
                    f"0.35 * {row['latency_weakness']:.6f} + "
                    f"0.20 * {row['data_sufficiency']:.6f})"
                ),
                "base_score": row["base_score"],
                "base_rank": int(row["base_rank"]),
                "reason": row["priority_reason"],
                "data_quality_note": row["data_quality_note"],
            }
        )

    base_order = scenarios["base"].set_index("adm1_iso")["rank"]
    sensitivity = {}
    for name, scenario in scenarios.items():
        current = scenario.set_index("adm1_iso")["rank"]
        sensitivity[name] = [
            {
                "adm1_iso": iso,
                "rank": int(current.loc[iso]),
                "change_from_base": int(base_order.loc[iso] - current.loc[iso]),
            }
            for iso in base_order.index
        ]

    audit = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "grain": "one ADM1 region for Q4 2024",
        "method": "0-1 comparative percentile components combined into a 0-100 score",
        "weights": SCENARIOS,
        "persistence_policy": "Unavailable with one quarter; component is null and weight is zero in every scenario.",
        "base_ranking": scored[["adm1_iso", "adm1_name", "base_score", "base_rank", "priority_reason", "data_quality_note"]].to_dict(orient="records"),
        "three_region_traces": traces,
        "sensitivity": sensitivity,
        "outputs": {
            "csv": csv_path.as_posix(),
            "parquet": parquet_path.as_posix(),
            "figures": [path.as_posix() for path in figures],
        },
        "interpretation": "Priority is a transparent hypothesis generator, not a fault diagnosis or probability.",
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--parquet", type=Path, default=DEFAULT_PARQUET)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--figure-dir", type=Path, default=DEFAULT_FIGURE_DIR)
    args = parser.parse_args()
    print(json.dumps(run_scoring(args.input, args.csv, args.parquet, args.audit, args.figure_dir), indent=2))


if __name__ == "__main__":
    main()
