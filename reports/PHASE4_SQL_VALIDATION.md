# Phase 4 SQLite and KPI Validation

Run date: 2026-10-19

## Database build

- Engine: SQLite 3.53.1
- Fact table: `fact_tile_performance`
- Fact grain: one `(quadkey, period_start)` row
- Fact rows: 15,956
- Region dimension rows: 8
- Duplicate fact keys: 0
- Foreign-key errors: 0
- `PRAGMA integrity_check`: `ok`
- Database size: 6,967,296 bytes

The generated database is `data/processed/network_performance.sqlite`. It is excluded from Git and rebuilt from the validated GeoParquet source.

## SQL analyses

Fifteen named queries execute successfully and export CSV results under `reports/generated/sql/`:

1. Dataset overview
2. Overall speed KPIs
3. Overall latency KPIs
4. Loaded-latency KPIs
5. Quality-control totals
6. Quarter coverage
7. Regional measurement volume
8. Regional weighted performance
9. Weighted-versus-unweighted regional gap
10. Regional window-function rankings
11. Regional measurement-volume mix
12. Regional loaded-latency missingness
13. Download-speed deciles using `NTILE`
14. Low-speed/high-latency investigation candidates with a minimum-volume rule
15. Regional tests-per-device intensity

Query 14 returns 65 candidate tiles. This is a transparent screening query, not a fault classification or the Phase 6 composite score.

## Python reconciliation

| Metric | Python | SQLite | Difference | Result |
|---|---:|---:|---:|---|
| Tiles | 15,956 | 15,956 | 0 | Pass |
| Tests | 62,785 | 62,785 | 0 | Pass |
| Devices | 29,693 | 29,693 | 0 | Pass |
| Unweighted download Mbps | 36.078124655302084 | 36.078124655302084 | 0 | Pass |
| Test-weighted download Mbps | 37.625393756470494 | 37.625393756470494 | 0 | Pass |
| Test-weighted upload Mbps | 16.039675017918288 | 16.03967501791829 | 3.55e-15 | Pass |
| Test-weighted idle latency ms | 31.13791510711157 | 31.13791510711157 | 0 | Pass |
| Complete loaded-latency tiles | 15,483 | 15,483 | 0 | Pass |

Tolerance: absolute difference no greater than `1e-9`. The tiny upload difference is ordinary floating-point representation and is far below tolerance.

## Interpretation

- The weighted download KPI is higher than the unweighted tile mean, demonstrating that the two statistics answer different questions.
- Regional rankings must retain their denominators and measurement-volume context.
- Summed device counts are contributions by tile, not a count of unique people across Bangladesh.
- Only one quarter is available, so persistence and quarter-over-quarter SQL claims remain out of scope.
