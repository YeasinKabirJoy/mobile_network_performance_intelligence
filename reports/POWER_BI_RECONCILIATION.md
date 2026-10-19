# Phase 7 Power BI Reconciliation

## Method

The curated Power BI CSVs are generated from the Phase 4 SQLite fact table. This report compares SQLite results with a Pandas recalculation over the exact imported rows, using formulas equivalent to the explicit DAX measures. The machine-readable evidence is `reports/generated/power_bi_reconciliation.json`.

## Expected dashboard values

Values below are populated by the export command and must be checked in Power BI Desktop after model assembly.

| Filter | Tiles | Tests | Devices* | Weighted download Mbps | Weighted upload Mbps | Weighted idle latency ms |
|---|---:|---:|---:|---:|---:|---:|
| All Bangladesh | 15,956 | 62,785 | 29,693 | 37.625394 | 16.039675 | 31.137915 |
| Dhaka | 4,420 | 25,540 | 11,811 | 33.797656 | 15.061621 | 26.380619 |
| Rajshani | 1,582 | 4,706 | 2,356 | 34.166719 | 13.874831 | 43.252231 |

\* Devices is the sum of tile-level unique-device counts. It is not a deduplicated count of people, subscribers, or devices across the entire filtered geography.

## Result

The generated import-layer reconciliation passes all six metrics for the default view and both regional filters at an absolute tolerance of `1e-9`. Desktop acceptance remains a manual checkpoint because native Power BI window control was unavailable in this execution environment. When assembled, the cards should match after display rounding; any larger difference is a model or measure defect.
