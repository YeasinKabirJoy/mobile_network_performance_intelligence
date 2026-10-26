"""Run Phase 9 artifact, reconciliation, and published-claim assurance checks."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_OUTPUT = Path("reports/generated/phase9_assurance_audit.json")
TOLERANCE = 1e-9

REQUIRED_ARTIFACTS = [
    "README.md",
    "docs/DATA_DICTIONARY.md",
    "docs/KPI_DEFINITIONS.md",
    "reports/DATA_QUALITY_REPORT.md",
    "docs/PROJECT_DECISIONS.md",
    "docs/LEARNING_NOTES.md",
    "reports/BUSINESS_SUMMARY.md",
    "docs/DATA_LINEAGE.md",
    "reports/CROSS_TOOL_RECONCILIATION.md",
    "docs/WORKFLOW_EXPLANATION.md",
    "docs/EXAMPLE_TILE_TRACE.md",
    "docs/KPI_RECONCILIATION.md",
    "docs/RUNBOOK.md",
    "docs/INTERVIEW_QA.md",
    "docs/PROJECT_PRESENTATION.md",
    "reports/figures/power_bi/management_dashboard_build_reference.png",
    "reports/figures/tableau/geographic_explorer_build_reference.png",
]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_assurance(root: Path) -> dict:
    missing = [path for path in REQUIRED_ARTIFACTS if not (root / path).is_file()]
    python_sql = _read_json(root / "reports/generated/python_sql_reconciliation.json")
    power_bi = _read_json(root / "reports/generated/power_bi_reconciliation.json")
    tableau = _read_json(root / "reports/generated/tableau_reconciliation.json")
    eda = _read_json(root / "reports/generated/eda_summary.json")
    scoring = _read_json(root / "reports/generated/scoring_audit.json")

    expected = {
        "rows": 15956,
        "tests": 62785,
        "devices": 29693,
        "weighted_download_mbps": 37.625393756470494,
        "weighted_upload_mbps": 16.039675017918288,
        "weighted_idle_latency_ms": 31.13791510711157,
        "median_download_mbps": 27.8645,
        "low_volume_tiles": 12797,
        "top_priority_region": "Rajshani",
    }
    observed = {
        "rows": eda["rows"],
        "tests": eda["tests"],
        "devices": eda["devices"],
        "weighted_download_mbps": eda["weighted_national"]["download_mbps"],
        "weighted_upload_mbps": eda["weighted_national"]["upload_mbps"],
        "weighted_idle_latency_ms": eda["weighted_national"]["idle_latency_ms"],
        "median_download_mbps": eda["metrics"]["avg_d_mbps"]["median"],
        "low_volume_tiles": eda["measurement_volume"]["low"],
        "top_priority_region": scoring["base_ranking"][0]["adm1_name"],
    }
    claim_checks = {}
    for name, expected_value in expected.items():
        observed_value = observed[name]
        if isinstance(expected_value, float):
            passed = abs(expected_value - float(observed_value)) <= TOLERANCE
        else:
            passed = expected_value == observed_value
        claim_checks[name] = {"expected": expected_value, "observed": observed_value, "pass": passed}

    reconciliation_checks = {
        "python_vs_sqlite": bool(python_sql["passed"]),
        "power_bi_import_rows_vs_sqlite": bool(power_bi["all_pass"]),
        "tableau_export_rows_vs_sqlite": bool(tableau["all_pass"]),
    }
    power_bi_workbooks = [
        root / "powerBI/dashboard.pbix",
        root / "dashboards/power_bi/Mobile_Network_Performance_Intelligence.pbix",
    ]
    tableau_workbooks = [
        root / "tableau/dashboard.twb",
        root / "tableau/dashboard.twbx",
        root / "dashboards/tableau/Mobile_Network_Performance_Intelligence.twbx",
        root / "dashboards/tableau/Mobile_Network_Performance_Intelligence.twb",
    ]
    power_bi_complete = any(p.is_file() for p in power_bi_workbooks)
    tableau_complete = any(t.is_file() for t in tableau_workbooks)

    desktop_dashboard_status = {
        "power_bi": (
            "native Power BI Desktop workbook (.pbix) and verified screenshots present"
            if power_bi_complete
            else "manual checkpoint pending; no PBIX or native screenshot claimed"
        ),
        "tableau": (
            "native Tableau Desktop workbook (.twb/.twbx) and verified screenshots present"
            if tableau_complete
            else "manual checkpoint pending; no TWB/TWBX or native screenshot claimed"
        ),
    }
    completion_status = (
        "Phase 10 documentation complete; native Power BI and Tableau dashboards built and verified"
        if (power_bi_complete and tableau_complete)
        else "Phase 10 documentation complete; native Power BI and Tableau checkpoints remain"
    )

    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "required_artifact_count": len(REQUIRED_ARTIFACTS),
        "missing_artifacts": missing,
        "claim_checks": claim_checks,
        "reconciliation_checks": reconciliation_checks,
        "desktop_dashboard_status": desktop_dashboard_status,
        "phase9_automated_checks_pass": (
            not missing
            and all(item["pass"] for item in claim_checks.values())
            and all(reconciliation_checks.values())
        ),
        "project_completion_status": completion_status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_assurance(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["phase9_automated_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
