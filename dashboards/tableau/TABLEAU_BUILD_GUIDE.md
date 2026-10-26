# Tableau Geographic Explorer Build Guide

## Status and purpose

The Tableau-ready flat extract, field dictionary, calculated fields, worksheet/dashboard specification, native workbook (`tableau/dashboard.twb`), actual dashboard screenshot, selected-tile trace, and cross-tool reconciliation evidence are complete and verified.

The dashboard is an exploratory companion to the Power BI management view. It is designed for map-led selection, distribution inspection, and tile detail—not executive status reporting or fault diagnosis.

## Connect and prepare fields

1. Connect Tableau Desktop to `data/processed/tableau/TableauTileExplorer.csv` as a text file.
2. Confirm 15,956 rows and 24 fields.
3. Assign geographic roles: `longitude` = Longitude and `latitude` = Latitude.
4. Convert `period_start` to Date; keep `quarter_label`, `adm1_iso`, `adm1_name`, `quadkey`, `measurement_volume`, and notes as dimensions.
5. Keep performance, test/device, score, and rank fields as measures. Set `quadkey` to String and default aggregation for identifiers to Attribute or None.
6. Create every formula in `CALCULATED_FIELDS.txt` and format Mbps/ms to two decimals and percentages to one decimal.

The export is intentionally flat. Region-quarter score attributes repeat on tile rows, so use `MIN`, not `SUM`, for score and rank. The current one-quarter grain prevents a supported trend sheet; retain the quarter filter so the design is ready for future appended periods.

## Worksheets

### 1. Tile Map

- Columns: generated Longitude from `longitude`; Rows: generated Latitude from `latitude`.
- Marks: Circle.
- Detail: `Tile-Quarter Key`; Color: `avg_d_mbps`; optional Size: `tests` with a narrow range.
- Use a perceptually ordered sequential palette. Fix the visible color range to the current p5-p95 values only if the legend states that clipping; do not filter extreme rows away.
- Tooltip: quadkey, quarter, region, coordinates, download/upload Mbps, idle and loaded latency, tests, devices, volume category, quality note, priority score/rank, and the warning that the mark is a measurement tile—not coverage or a tower.

### 2. Region Comparison

- Rows: `adm1_name`; Columns: `Test-Weighted Download Mbps`.
- Sort ascending; horizontal bars; label to two decimals.
- Add `Test-Weighted Upload Mbps`, `Test-Weighted Idle Latency Ms`, tests, and tile count to tooltip.

### 3. Latency Distribution

- Columns: `adm1_name`; Rows: `avg_lat_ms`.
- Use a box-and-whisker plot and hide individual outlier marks only for display readability; do not filter the underlying records.
- Tooltip should disclose region tile count and test count.

### 4. Investigation Priority

- Region bars or text table using `Regional Priority Score`, rank, `priority_reason`, and `data_quality_note`.
- Sort by rank ascending. Use red as attention, not as confirmed fault status.

### 5. Selected Tile Details

- Text table showing one selected `Tile-Quarter Key` with all tooltip fields.
- Include a contribution line: `avg_d_mbps * tests`, explaining that this numerator contribution is divided by the region's total tests together with all other tile contributions.

### 6. Quarter Comparison

- Do not create a line chart from the present data: only Q4 2024 is available.
- Show the quarter filter and an annotation: "One quarter available; trend view activates after validated periods are appended."

## Dashboard and actions

Use a fixed 1,440 x 900 desktop canvas:

- Top: title, quarter filter, region filter, evidence warning.
- Left two-thirds: Tile Map.
- Upper right: Region Comparison and Investigation Priority.
- Bottom left: Latency Distribution.
- Bottom right: Selected Tile Details.

Create these actions:

1. **Map Select -> Details:** Filter action from Tile Map to Selected Tile Details, run on Select, clearing selection shows all values only if the details sheet is designed not to aggregate misleadingly; otherwise exclude all values.
2. **Region Select -> Explorer:** Filter action from Region Comparison and Investigation Priority to Tile Map, Latency Distribution, and details, run on Select; clearing shows all regions.
3. **Cross-highlight:** Highlight action on `adm1_name` across the map and regional worksheets.

Apply the quarter and region filters to all worksheets using the same data source. Confirm that selecting a map mark exposes exactly one tile-quarter record.

## Required validation

Reconcile the calculated fields under these conditions:

1. Quarter = 2024-Q4; Region = All.
2. Quarter = 2024-Q4; Region = Dhaka.
3. Quarter = 2024-Q4; Region = Rajshani.
4. Select tile `1320222021021031`; verify every detail in `reports/TABLEAU_RECONCILIATION.md`.

## Save, package, and publish

- Save locally as `.twb` while developing. After validation, use **File > Save As > Tableau Packaged Workbook (.twbx)** so the local text source is included.
- Before Tableau Public, remember that published workbooks and their extracted data are publicly accessible. Review the Ookla CC BY-NC-SA 4.0 requirements, geoBoundaries attribution, noncommercial purpose, and the absence of sensitive enrichment.
- Tableau Public creates an extract and does not automatically refresh a local CSV. Regenerate the CSV, refresh/re-publish deliberately, and rerun reconciliation.
- Never publish credentials, private telemetry, unpublished operator data, or precise sensitive locations with this public dataset.

## Concepts

A dimension slices or identifies marks; a measure is aggregated. Discrete fields create headers; continuous fields create axes. The Marks card controls mark type and encodings. Context filters run before dependent filters and table calculations, so add them only when order-of-operations behavior is intended. Parameters are user-controlled values, sets define membership, and dashboard actions connect selections to filtering or highlighting. Tableau's exploratory strength is direct interaction with marks; Power BI's companion page emphasizes governed management KPIs.
