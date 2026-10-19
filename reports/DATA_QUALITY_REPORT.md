# Data Quality Report - Phase 3

Run date: 2026-10-19

## Grain and population

- Input grain: one geographically retained tile for Q4 2024.
- Enforced output key: `(quadkey, period_start)`.
- Input rows: 15,956.
- Output rows: 15,956.
- Removed rows: 0.

No row was removed merely for weak speed, high latency, low measurement volume, or missing loaded latency.

## Exclusion audit

| Potential exclusion reason | Rows |
|---|---:|
| Missing required value | 0 |
| Duplicate tile-period key | 0 |
| Invalid or missing coordinates | 0 |
| Geometry/centroid coordinate mismatch | 0 |
| Nonpositive or inconsistent counts | 0 |
| Negative performance measurement | 0 |
| Invalid period | 0 |
| Invalid region assignment | 0 |

These are reusable rejection rules. A future source can produce nonzero exclusions, which will be disclosed rather than silently dropped.

## Missing values

| Field | Null rows before | Null rows after | Policy |
|---|---:|---:|---|
| `avg_lat_down_ms` | 370 | 370 | Preserve null |
| `avg_lat_up_ms` | 184 | 184 | Preserve null |
| Other fields | 0 | 0 | Required where structurally necessary |

There are 15,483 rows with both loaded-latency values. Because some rows are missing both fields, individual null counts do not sum directly to the incomplete-row count.

## Measurement-volume categories

| Category | Rule | Rows |
|---|---|---:|
| Low | 1-4 tests | 12,797 |
| Medium | 5-19 tests | 2,732 |
| High | 20+ tests | 427 |

The categories communicate evidence volume. They do not claim statistical representativeness and do not determine whether a row is valid.

## Unit conversion verification

The implemented rule is `Mbps = kbps / 1,000`. Source kbps values remain available for lineage.

| quadkey | download kbps | download Mbps | upload kbps | upload Mbps |
|---|---:|---:|---:|---:|
| `1231331013033233` | 5,086 | 5.086 | 24,564 | 24.564 |
| `1231331013211011` | 11,751 | 11.751 | 24,777 | 24.777 |
| `1231331013212303` | 9,207 | 9.207 | 2,641 | 2.641 |
| `1231331013213132` | 49,008 | 49.008 | 16,555 | 16.555 |
| `1231331013230010` | 21,726 | 21.726 | 13,664 | 13.664 |

All 15,956 download and upload conversions passed exact numeric validation within floating-point tolerance.

## Suspicious but preserved values

- One row has idle latency equal to zero and was preserved for later investigation.
- Very low speeds and high latency values remain present because the source counts, types, and keys are valid.
- Phase 5 EDA will study their distributions; Phase 3 does not relabel them as faults or automatically delete them.

## Outputs

- Processed GeoParquet: `data/processed/bgd_mobile_tiles_2024_q4_clean.parquet`
- Processed CSV: `data/processed/bgd_mobile_tiles_2024_q4_clean.csv`
- Cleaning evidence: `reports/generated/cleaning_audit.json`
- Validation evidence: `reports/generated/processed_validation.json`

The exact output sizes and SHA-256 hashes are recorded in the machine-readable cleaning audit because they are regenerated artifacts.
