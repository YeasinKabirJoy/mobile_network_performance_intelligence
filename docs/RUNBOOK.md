# Clean-Environment Reproduction Runbook

## Prerequisites

- Windows 10/11 with PowerShell.
- Python 3.11+ and `uv` recommended.
- Enough disk space for the 195 MB raw Parquet plus generated files.
- Power BI Desktop and Tableau Desktop only for the native dashboard checkpoints.
- Internet access for the official source and boundary download if raw inputs are absent.

## 1. Clone and create the environment

```powershell
git clone <repository-url>
cd mobile_network_performance_intelligence
uv venv --python 3.11 .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Expected result: imports for DuckDB, GeoPandas, Pandas, PyArrow, Shapely, Matplotlib, Seaborn, and Jupyter succeed.

If activation is restricted, run `.\.venv\Scripts\python.exe` explicitly. If geospatial wheels fail, confirm Python architecture/version and reinstall from binary wheels rather than compiling ad hoc.

## 2. Obtain and verify source inputs

Download the official Q4 2024 mobile Parquet to:

`data/raw/2024-10-01_performance_mobile_tiles.parquet`

Official URL:

`https://ookla-open-data.s3.amazonaws.com/parquet/performance/type=mobile/year=2024/quarter=4/2024-10-01_performance_mobile_tiles.parquet`

Run:

```powershell
python -m src.inspect_source
```

Expected evidence: 3,551,267 source rows, 195,139,957 bytes, SHA-256 `08DFBBB3ABF765A9524AD0B002769F04F880B3FE1502452A819F4DECB6B02B60`, and 49,213 bounding-box candidates. Re-accessed source data can legitimately change due to provider reaggregation; investigate checksum/count differences rather than forcing the historical result.

Failure recovery:

- HTTP/download failure: retry the official URL or documented official Shapefile fallback; never fabricate the file.
- Size/hash mismatch: confirm download completion and source access date; preserve new evidence.
- Schema change: inspect column names/types and update projection, dictionary, validation, and downstream reconciliation together.

## 3. Geographic extraction

```powershell
python -m src.extract
```

Expected result: 15,956 retained Bangladesh rows in all eight ADM1 regions, zero ambiguous centroids, zero duplicate retained quadkeys, and a geographic validation figure.

Failure recovery:

- Empty spatial match: inspect both CRS values, coordinate order, geographic extent, and boundary validity.
- Excessive memory: confirm only required Parquet columns and bbox candidates are loaded.
- Changed region totals: inspect boundary release, predicate, centroid rule, source period, and unmatched candidates.

## 4. Clean and validate

```powershell
python -m src.clean
python -m src.validate
```

Expected result: 15,956 processed rows, no invalid exclusions in the current source, 15,483 complete loaded-latency rows, and clean CSV/Parquet files. Speeds are divided by 1,000, not 1,024.

Failure recovery:

- Duplicate key: inspect `(quadkey, period_start)` and do not arbitrarily retain a row.
- Invalid counts/coordinates: inspect the source record and rule before exclusion.
- Missing loaded latency: retain null and eligibility flag; never replace with zero.
- Changed volume threshold: expect labels/warnings to change, not performance values or row counts.

## 5. Build SQLite and run SQL

```powershell
python -m src.build_database
python -m src.run_sql
python -m src.reconcile
```

Expected result: `network_performance.sqlite` with 15,956 fact rows and 8 region rows; integrity `ok`; 15 SQL result CSVs; eight Python/SQLite comparisons pass.

Failure recovery:

- Locked database: close SQLite/BI clients and retry.
- Foreign-key error: compare fact region codes with `dim_region`.
- Integer division: ensure a real operand such as `SUM(tests) * 1.0`.
- Weighted mismatch: compare filter, numerator, denominator, units, and null eligibility.

## 6. Run EDA

```powershell
python -m src.eda
```

Expected result: eight figures, an EDA contact sheet, and `eda_summary.json`. Key checks include 27.8645 Mbps median tile download and 80.20% low-volume tiles.

Failure recovery:

- Flattened colors: verify only the display scale is percentile-clipped, not the data.
- Different correlations: confirm identical row filters and correlation method.
- False time chart: stop; only one quarter is present.

## 7. Generate priority scoring

```powershell
python -m src.score
```

Expected result: eight region scores, Rajshani rank 1 at 86.7857, three calculation traces, and two sensitivity figures. Persistence remains null/zero-weight.

Failure recovery:

- Missing required input: scoring should fail explicitly; do not impute silently.
- Rank changes: inspect weights, metric direction, ties, and comparison set.
- Score interpreted as fault: correct the label and require direct operational evidence.

## 8. Regenerate BI imports and reconcile

```powershell
python -m src.export_power_bi
python -m src.export_tableau
```

Expected result: four Power BI CSVs, one 15,956-row Tableau explorer CSV, a 24-field dictionary, two build references, and 18 passing comparisons for each BI handoff.

Power BI Desktop:

1. Import the four files under `data/processed/power_bi/`.
2. Create relationships and measures exactly as documented in `dashboards/power_bi/`.
3. Verify All, Dhaka, and Rajshani values.
4. Save PBIX/PBIP and capture real screenshots.

Tableau Desktop:

1. Connect to `data/processed/tableau/TableauTileExplorer.csv`.
2. Apply roles and calculations from `dashboards/tableau/`.
3. Build sheets/actions and select quadkey `1320222021021031`.
4. Verify All, Dhaka, Rajshani, and tile details; save TWB/TWBX and capture real screenshots.

Failure recovery:

- File not found after repository move: update the data-source path and refresh.
- KPI mismatch: remove implicit aggregation, check relationship/filter direction, and compare exact eligibility.
- Duplicate priority total in Tableau: use `MIN(base_score)`, never sum repeated regional values.
- Map in wrong location: assign explicit longitude/latitude roles and confirm coordinate order.
- Tableau Public: local CSVs do not auto-refresh; republish after regeneration and license review.

## 9. Generate final evidence and assurance

```powershell
python -m src.final_trace
python -m src.assure
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

Expected result: real tile/KPI trace JSON, no missing assurance artifacts, verified headline claims, passing reconciliation layers, and all unit tests passing.

## 10. Execute notebooks

Open and run notebooks 01-06 in order. In automated environments, execute with Jupyter `nbconvert --execute`. Expected result: no error outputs and values matching generated JSON/reports.

## Rebuild order after changes

Always rebuild from the earliest changed stage. A boundary change requires Phase 2 onward. A cleaning-rule change requires Phase 3 onward. A SQL formula change requires database/query reconciliation and both BI definitions. A display-only style change does not justify recalculating source metrics but still requires visual QA.
