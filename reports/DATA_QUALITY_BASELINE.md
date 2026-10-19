# Data Quality Baseline - Phase 1

Inspection run: 2026-10-19. Machine-readable evidence: `reports/generated/source_inspection.json`.

## Source integrity and schema

- Local size: 195,139,957 bytes, equal to the remote `Content-Length` observed on the access date.
- SHA-256: `08DFBBB3ABF765A9524AD0B002769F04F880B3FE1502452A819F4DECB6B02B60`
- Rows: 3,551,267
- Columns: 11
- Duplicate `quadkey` values: 0
- Observed fields: `quadkey`, `tile`, `tile_x`, `tile_y`, `avg_d_kbps`, `avg_u_kbps`, `avg_lat_ms`, `avg_lat_down_ms`, `avg_lat_up_ms`, `tests`, `devices`
- Physical types: text for `quadkey` and WKT `tile`; double for centroid coordinates; integer types for metrics and counts.
- Global sanity checks found no nonpositive test/device counts, no rows where devices exceeded tests, no nonpositive download/upload averages, and no negative idle latency.
- Observed global centroid ranges were longitude -179.9973 to 179.9918 and latitude -71.9917 to 79.3955.

## Missingness

| Field | Null rows | Percent of source |
|---|---:|---:|
| `avg_lat_down_ms` | 89,345 | 2.516% |
| `avg_lat_up_ms` | 52,757 | 1.486% |
| Every other source field | 0 | 0.000% |

Loaded-latency nulls are expected according to the official source documentation and must not be replaced with zero.

## Bangladesh coverage verification

- Conservative bounding-box candidates: 49,213 rows.
- Centroids inside an official Bangladesh ADM1 polygon: 15,956 rows.
- Matched records contain 62,785 tests and 29,693 devices in aggregate. These are participation counts, not subscribers or residents.
- Within the matched records, loaded-download latency is missing for 370 rows and loaded-upload latency for 184 rows; no row has fewer tests than devices.
- All eight boundary features received matches: Barisal 961, Chittagong 4,022, Dhaka 4,420, Khulna 1,467, Mymensingh 709, Rajshani 1,582, Rangpur 1,524, and Sylhet 1,271.
- `Rajshani` is retained here exactly as supplied by the selected geoBoundaries file; naming normalization is a later explicit decision.

This verifies that Q4 2024 contains suitable Bangladesh measurements. Counts are inspection evidence, not the final extraction audit.

## Representative verified Bangladesh records

These are the five highest-test centroid matches returned by the deterministic inspection ordering. Values remain in source units.

| quadkey | longitude | latitude | download kbps | upload kbps | idle latency ms | tests | devices |
|---|---:|---:|---:|---:|---:|---:|---:|
| `1320222021021031` | 90.4147 | 23.7929 | 28,630 | 15,908 | 43 | 319 | 45 |
| `1320222021023110` | 90.4312 | 23.7627 | 41,388 | 12,599 | 18 | 248 | 23 |
| `1320222313203013` | 92.5241 | 22.7078 | 163,882 | 5,499 | 91 | 235 | 8 |
| `1231333312103211` | 89.5358 | 22.8547 | 52,560 | 15,647 | 21 | 227 | 4 |
| `1320222021003321` | 90.4257 | 23.8130 | 45,621 | 20,852 | 20 | 200 | 58 |

These rows are real observations but are not yet cleaned, assigned through the audited Phase 2 pipeline, or suitable for performance conclusions.

## Interpretation boundary

The point-in-polygon check establishes Bangladesh availability. It does not constitute the saved, audited country extraction, border-policy analysis, geometry validation, or final ADM1 assignment required in Phase 2.
