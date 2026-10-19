# Phase 8 Tableau Reconciliation and Tile Selection

## Import-layer reconciliation

The Tableau flat CSV was regenerated from SQLite and recalculated with formulas equivalent to the documented Tableau calculated fields. All six KPIs pass for all three required filter states at absolute tolerance `1e-9`.

| Filter | Tiles | Tests | Devices* | Weighted download Mbps | Weighted upload Mbps | Weighted idle latency ms |
|---|---:|---:|---:|---:|---:|---:|
| All Bangladesh | 15,956 | 62,785 | 29,693 | 37.625394 | 16.039675 | 31.137915 |
| Dhaka | 4,420 | 25,540 | 11,811 | 33.797656 | 15.061621 | 26.380619 |
| Rajshani | 1,582 | 4,706 | 2,356 | 34.166719 | 13.874831 | 43.252231 |

\* Devices is a sum of tile-level unique counts and is not globally deduplicated, population, or subscribers.

The only nonzero computational difference is approximately `1.78e-15` Mbps for Rajshani upload, caused by floating-point representation.

## Real selected-tile checkpoint

The deterministic selection rule chooses the highest-test tile, breaking ties by ascending quadkey:

- Quadkey: `1320222021021031`
- Quarter: 2024-Q4
- Region: Dhaka (`BD-C`)
- Centroid: longitude 90.4147, latitude 23.7929
- Download: 28.630 Mbps
- Upload: 15.908 Mbps
- Idle latency: 43 ms
- Tests: 319
- Devices: 45
- Volume category: high
- Tile download numerator contribution: 9,132.97 Mbps-tests

Dhaka's full numerator is 863,192.131 Mbps-tests and denominator is 25,540 tests, producing 33.797656 Mbps. This tile contributes about 1.058% of that numerator. Its region has priority score 55.3571 and rank 4. Selecting it demonstrates linked details; it does not identify a tower, subscriber, operator, outage, or fault.

## Desktop acceptance

After assembling the workbook, check the three KPI filter states and the selected tile in the actual views. The available execution environment could not attach to Tableau Desktop's native window, so visual actions and a `.twbx` remain the learner checkpoint rather than an unverified artifact.
