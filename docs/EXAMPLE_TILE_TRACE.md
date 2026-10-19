# Real Tile Trace - Quadkey 1320222021021031

This trace is generated from actual project artifacts by `python -m src.final_trace`. The machine-readable evidence is `reports/generated/final_tile_trace.json`. No values below are illustrative.

## 1. Raw source record

| Field | Raw value |
|---|---:|
| Quadkey | `1320222021021031` |
| Tile centroid | 90.4147 longitude, 23.7929 latitude |
| Download | 28,630 kbps |
| Upload | 15,908 kbps |
| Idle latency | 43 ms |
| Download-loaded latency | 1,109 ms |
| Upload-loaded latency | 1,298 ms |
| Tests | 319 |
| Devices | 45 |

The source polygon spans approximately 90.41199-90.41748 longitude and 23.79037-23.79540 latitude. This row is one quarterly map-tile aggregate, not a tower or an individual test.

## 2. Geographic extraction

The centroid satisfies the Bangladesh candidate bounding box and intersects the geoBoundaries ADM1 polygon `BD-C`, Dhaka, in EPSG:4326. It was not a boundary tie. The selected centroid rule assigns one reporting region and prevents duplicate aggregation; it does not measure how much of the polygonal tile overlaps Dhaka.

## 3. Cleaning transformations

- `28,630 kbps / 1,000 = 28.630 Mbps`.
- `15,908 kbps / 1,000 = 15.908 Mbps`.
- Both loaded-latency values are present, so `loaded_latency_complete = true`.
- 319 tests places the row in the `high` evidence-volume category (20+ tests).
- The row passes coordinate, count, range, period, region, and composite-key checks.
- `quality_note = none`; this does not certify network quality, only that no configured row warning applies.

## 4. SQLite row

The row is stored in `fact_tile_performance` at key `(quadkey='1320222021021031', period_start='2024-10-01')` with `adm1_iso='BD-C'`. A direct query is:

```sql
SELECT *
FROM fact_tile_performance
WHERE quadkey = '1320222021021031'
  AND period_start = '2024-10-01';
```

SQLite stores the raw kbps values, derived Mbps values, coordinates, latency, counts, quality fields, and tile WKT so transformation lineage remains visible.

## 5. Contribution to Dhaka's weighted-download KPI

The tile contributes:

`28.630 Mbps * 319 tests = 9,132.97 Mbps-tests`

Across Dhaka Q4 2024:

- Numerator: 863,192.131 Mbps-tests.
- Denominator: 25,540 tests.
- Result: `863,192.131 / 25,540 = 33.797655873 Mbps`.
- This tile supplies approximately 1.0580% of the numerator.

The tile is one input to the regional aggregate; it is not itself the regional result.

## 6. EDA presence

The tile participates in the download, upload, idle-latency, and test-volume distributions; the regional download boxplot; the download-latency scatter; and the geographic tile map. The figures use it as one observation and do not identify it as a fault.

## 7. Regional priority calculation

The score is defined at ADM1 level, not tile level. This tile contributes to Dhaka's aggregated inputs and therefore inherits Dhaka as context; it does not receive an independent anomaly score.

Dhaka components are:

- Speed weakness: 0.785714.
- Latency weakness: 0.000000.
- Data sufficiency: 1.000000.
- Persistence: unavailable and weighted 0.

`100 * (0.45 * 0.785714 + 0.35 * 0 + 0.20 * 1) = 55.357143`

Dhaka ranks 4th in the base scenario. Speed emphasis moves it to rank 3; latency emphasis moves it to rank 6. That movement shows that rank is decision-weight dependent.

## 8. BI export and dashboard behavior

The exact row is present in both `FactTilePerformance.csv` for Power BI and `TableauTileExplorer.csv` for Tableau. Expected filter/tooltip values are quadkey, Q4 2024, Dhaka, the two coordinates, 28.630/15.908 Mbps, 43 ms, 319 tests, and 45 devices.

The Tableau action specification selects this tile and filters the detail sheet. The Power BI tooltip specification exposes the same fields. Native Power BI/Tableau Desktop files and interactive selection remain manual checkpoints; the project does not claim that the row has been visually located in an unbuilt native workbook.

## 9. Cautious operational interpretation

An analyst may say this is a relatively high-volume public tile observation in Dhaka with 28.630 Mbps download and 43 ms idle latency in Q4 2024. The analyst may compare it with peers and inspect nearby patterns. They may not call it a tower fault, operator outage, coverage gap, congestion event, or subscriber experience without site inventory, operator identity, time-resolved telemetry, traffic/load, radio measurements, incidents, and field validation.
