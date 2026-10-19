# Power BI Management Dashboard Build Guide

## Status

The curated imports, model design, DAX, visual specification, static build reference, and reconciliation evidence are complete. This environment could launch Power BI Desktop but could not attach to its native window, so no `.pbix` or genuine Power BI screenshot is claimed. Follow the short Desktop procedure below to create the interactive report from the verified assets.

## Business purpose

The dashboard helps an analyst or regional operations manager compare public Q4 2024 mobile-performance measurements, identify regions for follow-up, and inspect the evidence-volume caveat. It must not be used to conclude that a tower, operator, outage, or root cause has been identified.

## Import model

Import these four generated files from `data/processed/power_bi/`:

| Power BI table | File | Grain |
|---|---|---|
| `FactTilePerformance` | `FactTilePerformance.csv` | One map tile for Q4 2024 |
| `DimRegion` | `DimRegion.csv` | One ADM1 region |
| `DimQuarter` | `DimQuarter.csv` | One available quarter |
| `FactRegionPriority` | `FactRegionPriority.csv` | One ADM1 region-quarter score |

Use Import mode. It keeps the portfolio artifact self-contained and avoids a machine-specific live SQLite connection. The curated files are regenerated from SQLite with `python -m src.export_power_bi`.

Create single-direction, one-to-many relationships:

- `DimRegion[adm1_iso]` to `FactTilePerformance[adm1_iso]`.
- `DimRegion[adm1_iso]` to `FactRegionPriority[adm1_iso]`.
- `DimQuarter[quarter_label]` to `FactTilePerformance[quarter_label]`.
- `DimQuarter[quarter_label]` to `FactRegionPriority[quarter_label]`.

Do not connect the two facts directly and do not enable bidirectional filtering. Mark identifier and label columns as "Do not summarize." Assign decimal-number types to Mbps/latency, whole numbers to tests/devices/ranks, and latitude/longitude geographic roles to the coordinate fields.

## Measures

Create every measure in `MEASURES.dax`; do not use implicit visual sums for performance metrics. `DIVIDE` handles a zero denominator safely. `CALCULATE` changes filter context, and `SUMX` reconstructs the documented test-weighted numerator row by row.

The device card is labeled "summed tile device counts." A device can contribute in more than one tile, so the measure is not a national unique-device count. Neither tests nor devices represent subscribers or population.

## Report page: Executive Overview

Canvas: 16:9, light gray background, dark navy headings, blue performance visuals, red investigation-priority visuals.

1. Header: "Mobile Network Performance Intelligence" plus `[Dashboard Scope]`.
2. Slicers: `DimQuarter[quarter_label]` and `DimRegion[adm1_name]`. Keep the quarter slicer visible even though only Q4 2024 is currently available.
3. KPI cards: `[Tiles]`, `[Tests]`, `[Devices]`, `[Test-Weighted Download Mbps]`, `[Test-Weighted Upload Mbps]`, and `[Test-Weighted Idle Latency Ms]`.
4. Clustered bar chart: `DimRegion[adm1_name]` by `[Test-Weighted Download Mbps]`, sorted ascending.
5. Clustered bar chart: `DimRegion[adm1_name]` by `[Test-Weighted Idle Latency Ms]`.
6. Priority table: rank, region, priority score, `priority_reason`, and `data_quality_note`, sorted by rank.
7. Map: latitude and longitude from the tile fact, color by `avg_d_mbps`, tooltip with quadkey, region, tests, devices, download/upload Mbps, idle latency, volume category, and quality note. Label it "measurement tiles," not coverage.
8. Warning card: `[Data Quality Warning]`.
9. Footer tooltip/caption: source period, public aggregate provenance, test-weighted definition, and "Priority is a hypothesis generator, not a fault diagnosis."

Set both slicers to filter every visual. Selecting a region bar should cross-filter the KPI cards, latency chart, map, and priority table. Disable any interaction that merely highlights a denominator while leaving the rest of a KPI unfiltered.

## Reconciliation checks

After refresh, compare the cards to `reports/POWER_BI_RECONCILIATION.md` under these exact states:

1. Quarter = 2024-Q4, Region = All.
2. Quarter = 2024-Q4, Region = Dhaka.
3. Quarter = 2024-Q4, Region = Rajshani.

The imported rows already reproduce SQLite to floating-point tolerance. A Desktop value outside the stated rounding implies a relationship, filter, data type, or DAX error.

## Refresh and deployment

1. From the repository root, rebuild SQLite and run `python -m src.export_power_bi`.
2. In Desktop, use **Transform data > Data source settings** if the repository path moved.
3. Select **Refresh**, then repeat all three reconciliation states.
4. Save locally as `.pbix` or, for source control, as a `.pbip` project under this folder.
5. Do not publish publicly until the Ookla CC BY-NC-SA attribution and noncommercial/share-alike conditions have been reviewed for the intended destination.

Power Query performs connection, data-type, column-selection, and reshaping work before data enters the model. DAX evaluates model measures after load and responds to report filter context. Import mode stores a local copy; DirectQuery would query a supported source at interaction time. This project chooses Import because the curated dataset is small and refresh is deliberately controlled by the reproducible pipeline.
