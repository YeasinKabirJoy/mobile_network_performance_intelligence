# End-to-End Workflow Explanation

## Completion status

The reproducible data pipeline, analysis, scoring, BI handoff assets, assurance, real-tile trace, KPI trace, runbook, interview preparation, and presentation material are complete. Native Power BI and Tableau workbook creation, genuine screenshots, and in-application filter/action validation remain manual Desktop checkpoints because native-window control was unavailable. Therefore the engineering documentation is complete, but the full dashboard acceptance condition is not falsely marked complete.

## 10A. Business decision workflow

### Users and decisions

- **Data analyst:** verifies source quality, calculates KPIs, explores distributions, and explains uncertainty.
- **Regional operations manager:** uses comparative evidence to choose where to request deeper technical investigation.
- **Planning team:** uses repeated, validated patterns with operational data to prioritize measurement, capacity study, or field-validation effort.

The project supports questions such as which regions have comparatively weaker public measurements, whether latency and speed patterns co-occur, how measurement volume affects confidence, and where follow-up evidence should be gathered. It cannot select a tower for repair, rank operators, prove coverage, identify outages, estimate subscriber experience, or attribute root cause.

### Realistic decision scenario

Rajshani has 34.1667 Mbps test-weighted download, 13.8748 Mbps upload, and 43.2522 ms idle latency. It is rank 1 at 86.7857 and remains first in every tested weight scenario. An operations manager may prioritize Rajshani for follow-up, review its 84.8% low-volume tile share, inspect clusters and loaded-latency completeness, acquire additional quarters, and request operator/site/traffic/incident evidence. The manager should not declare a network fault from these aggregates alone.

## 10B. Architecture and data lineage

```text
Ookla Q4 2024 mobile Parquet (3,551,267 global tiles)
           + geoBoundaries Bangladesh ADM1 polygons
           |
           v
src.inspect_source -> source evidence and coverage feasibility
           |
           v
src.extract -> bbox candidates (49,213) -> centroid-in-polygon (15,956)
           |
           v
src.clean + src.validate -> trusted tile-quarter Parquet/CSV
           |
           v
src.build_database -> SQLite fact_tile_performance + dim_region
           |
           +--> src.run_sql -> 15 named SQL results
           +--> src.reconcile -> Python/SQLite evidence
           +--> src.eda -> statistics, 8 figures, findings
           +--> src.score -> 8 ADM1 scores + sensitivity
           |
           +--> src.export_power_bi -> 4 star-model imports + DAX handoff
           +--> src.export_tableau -> flat map source + calculations/actions
           |
           v
src.final_trace + src.assure -> real trace, KPI reconciliation, claim checks
           |
           v
business summary, workflow guide, runbook, Q&A, presentation
```

SQLite replaces the guide's recommended DuckDB database by explicit learner choice. DuckDB remains a read-efficient inspection tool for Parquet; SQLite is the persisted analytical database.

### What breaks when upstream inputs change

- A source-column rename breaks projection, cleaning, database loading, exports, and trace scripts.
- A boundary release or spatial rule changes regional membership and every regional KPI/rank/dashboard.
- A cleaning or null rule changes eligible rows and denominators.
- A grain change invalidates keys, relationships, `COUNTD`, and score aggregation.
- A new quarter requires region-quarter priority uniqueness, persistence logic, and genuine time views.
- A weight change alters score/rank but not underlying performance KPIs.
- A BI relationship or filter change can break native results even when curated imports remain correct.

## 10C. File-by-file implementation tour

Each entry states purpose; inputs; main transformations/functions; outputs; callers; validation/error handling; and run command.

### Python modules

| File | Purpose | Inputs | Transformations/functions | Outputs | Called by | Validation/errors | Run |
|---|---|---|---|---|---|---|---|
| `src/config.py` | Central cleaning constants | None | Frozen `CleaningConfig` | Threshold values | Cleaning/tests | Typed immutable defaults | Imported |
| `src/inspect_source.py` | Verify raw source and Bangladesh feasibility | Raw Parquet, boundary GeoJSON | Schema/null/count/checksum and bbox/centroid checks | Source JSON | Notebook 01, learner | Missing file/schema and geometry checks | `python -m src.inspect_source` |
| `src/extract.py` | Efficient geographic assignment | Raw Parquet, ADM1 boundaries | Projection, bbox filter, EPSG:4326 centroid spatial predicate, tie policy | Interim GeoParquet, audit, map | Cleaning, Notebook 02 | CRS, validity, unmatched, duplicate and region checks | `python -m src.extract` |
| `src/clean.py` | Produce trusted tile-quarter data | Interim GeoParquet | Type/range/key validation, unit conversion, volume labels, null flags | Clean Parquet/CSV, audit | SQLite, EDA, scoring, BI | Exclusion reasons and hashes; weak values preserved | `python -m src.clean` |
| `src/validate.py` | Assert processed contract | Clean dataset | Schema, range, key, conversion and geography assertions | Validation JSON | Pipeline/user | Nonzero exit on failed assertion | `python -m src.validate` |
| `src/build_database.py` | Materialize SQLite model | Clean GeoParquet, schema SQL | Region dimension and tile fact load in temporary DB, atomic replacement | SQLite DB, audit | SQL/reconciliation/BI | Integrity, PK/FK, count and checksum checks | `python -m src.build_database` |
| `src/run_sql.py` | Execute named analyses | SQLite DB, SQL scripts | Split named blocks, execute, export | 15 CSVs, manifest | Reports/learner | Query parsing/execution failures visible | `python -m src.run_sql` |
| `src/reconcile.py` | Independently compare Python/SQLite | Clean Parquet, SQLite | Recalculate eight KPIs | Reconciliation JSON | Assurance | Per-metric tolerance/pass | `python -m src.reconcile` |
| `src/eda.py` | Descriptive analysis and visuals | Clean GeoParquet | Summary stats, correlations, weighted regions, plots | EDA JSON, 8 PNGs, contact sheet | Findings/scoring context | Explicit methods and single-quarter guardrail | `python -m src.eda` |
| `src/score.py` | Explainable regional priority | Clean GeoParquet | Regional aggregation, percentiles, components, weights, ranks, sensitivity | Priority CSV/Parquet, audit, 2 PNGs | BI exports/reports | Missing required values fail; weight/range tests | `python -m src.score` |
| `src/export_power_bi.py` | Reproducible Power BI imports | SQLite, priority CSV | Star-model CSVs, Import formulas, 3-filter reconciliation, preview | 4 CSVs, JSON, PNG | Power BI guide/assurance | Hashes and 18 comparisons | `python -m src.export_power_bi` |
| `src/export_tableau.py` | Reproducible Tableau explorer source | SQLite, priority CSV | Flat join, dictionary, selected-tile trace, 3-filter reconciliation, preview | CSV, dictionary, JSONs, PNG | Tableau guide/assurance | Match checks and 18 comparisons | `python -m src.export_tableau` |
| `src/assure.py` | Phase 9 claim/artifact gate | Generated JSON and docs | Required-file, headline-claim, reconciliation checks | Assurance JSON | Final validation | Nonzero exit on missing/failed check | `python -m src.assure` |
| `src/final_trace.py` | Real tile and KPI proof | Raw/interim/clean/SQLite/score/BI exports | Cross-layer lookup and Dhaka weighted KPI recomputation | 2 trace JSONs | Phase 10 docs/tests | Exact quadkey and tolerance assertions | `python -m src.final_trace` |

### SQL

| File | Purpose | Inputs | Logic | Outputs/callers | Validation | Run |
|---|---|---|---|---|---|---|
| `sql/schema.sql` | Define analytical grain and relationships | None | `dim_region`, `fact_tile_performance`, PK/FK/indexes/checks | SQLite model; database builder | Schema unit test, integrity/FK audit | Through `src.build_database` |
| `sql/kpis.sql` | Core dataset and KPI analyses | SQLite fact/dimension | Counts, weighted/unweighted means, latency eligibility, quality totals | Generated SQL CSVs | Python reconciliation | Through `src.run_sql` |
| `sql/regional_analysis.sql` | Regional/quarter/volume/ranking analyses | SQLite fact/dimension | CTEs, joins, CASE, windows, deciles and candidates | Generated SQL CSVs | 15-query parse test and result review | Through `src.run_sql` |

### Notebooks

| Notebook | Purpose | Inputs/logic | Outputs | Validation | Run |
|---|---|---|---|---|---|
| `01_source_review.ipynb` | Teach source inspection | Source audit/schema/representative rows | Executed narrative | No error outputs | Jupyter |
| `02_geographic_extraction.ipynb` | Teach bbox/spatial assignment | Extraction module/audit/map | Retained counts and geographic explanation | No error outputs | Jupyter |
| `03_data_cleaning.ipynb` | Teach types/nulls/quality | Cleaning/validation artifacts | Before/after and conversion examples | No error outputs | Jupyter |
| `04_sql_analytics.ipynb` | Teach SQLite KPIs/SQL | DB, named query results, reconciliation | Query walkthrough | No error outputs | Jupyter |
| `05_eda.ipynb` | Teach distributions/associations/maps | EDA module/figures/JSON | Real findings and caveats | Executed, no errors | Jupyter |
| `06_scoring.ipynb` | Teach score and sensitivity | Score module/audit/figures | Ranking and three traces | Executed, no errors | Jupyter |

### Dashboard assets

| Asset | Purpose | Inputs | Logic/configuration | Outputs/callers | Validation | Run/use |
|---|---|---|---|---|---|---|
| `dashboards/power_bi/MEASURES.dax` | Explicit governed measures | Four Power BI imports | `SUMX`, `DIVIDE`, eligible filters, warnings | Power BI visuals | Import-layer reconciliation; native pending | Create measures in Desktop |
| `dashboards/power_bi/MODEL_AND_BUILD_GUIDE.md` | Model/page/interaction/refresh specification | BI CSVs/DAX | Two facts, shared dimensions, single-direction filters | PBIX/PBIP authoring | Three filter targets | Follow in Desktop |
| `dashboards/tableau/CALCULATED_FIELDS.txt` | Tableau KPI definitions | Flat explorer CSV | Weighted calculations, COUNTD, null eligibility, repeated-score `MIN` | Tableau worksheets | Export-layer reconciliation; native pending | Create fields in Desktop |
| `dashboards/tableau/TABLEAU_BUILD_GUIDE.md` | Sheet/dashboard/action/publication specification | Explorer CSV/dictionary | Map, comparisons, distribution, details, actions | TWB/TWBX authoring | Three filters + real tile | Follow in Desktop |

Magic constants are isolated or documented: bbox (88.0-92.8, 20.5-26.7), volume bands (1-4, 5-19, 20+), score weights (45/35/20/0), Q4 2024 period, and tolerance `1e-9`.

## 10D. Real geographic tile trace

The complete trace is in `docs/EXAMPLE_TILE_TRACE.md`. Quadkey `1320222021021031` begins as a raw Q4 tile at 90.4147/23.7929 with 28,630 kbps download, is assigned to Dhaka, becomes 28.630 Mbps with a high-volume label, is stored in SQLite, contributes 9,132.97 Mbps-tests to Dhaka's 33.797655873 Mbps KPI, appears in seven EDA views, and contributes indirectly to Dhaka's regional priority score of 55.357143/rank 4. It is present in both BI exports; native tooltip selection remains pending.

## 10E. KPI trace across four environments

`docs/KPI_RECONCILIATION.md` uses Dhaka Q4 2024 test-weighted download. Python and SQLite both produce numerator 863,192.131, denominator 25,540, and result 33.797655873 Mbps. Power BI and Tableau import/export recalculations match, while their native visual status is pending. This is a partial four-environment acceptance, not a fabricated pass.

## 10F. Key design decisions

| Subject | Choice and reason | Alternative/tradeoff | Failure scenario and validation |
|---|---|---|---|
| Parquet processing | Project columns and bbox-filter candidates; efficient typed scans | CSV is simpler but larger and weakly typed | Schema/memory change; inspect schema/counts and hashes |
| Bangladesh extraction | Bbox then precise ADM1 centroid predicate | Full global spatial join is expensive | Empty/wrong match; check CRS/extents/predicate |
| CRS | EPSG:4326 for source centroids and boundaries | Projected CRS needed for metric area/distance | Misplaced data; inspect CRS and plotted overlay |
| Centroid vs polygon | One centroid owner per tile prevents duplicates | Overlap allocation is more spatially faithful but complex | Border sensitivity; audit ties/unmatched and state limitation |
| Nulls/outliers | Preserve weak/zero values; loaded-latency null stays null | Dropping/imputation simplifies but biases | Denominator distortion; audit nulls and eligibility |
| Grain | `(quadkey, period_start)` | Tile-only key blocks valid repeated quarters | Duplicate joins/counts; enforce PK and tests |
| Weighted aggregation | `SUM(metric*tests)/SUM(tests)` | Unweighted mean answers typical-tile question | Wrong denominator/unit; Python/SQLite/BI reconciliation |
| Time | One Q4 2024 period; no trend/persistence | Fabricated daily/quarter trend is invalid | New periods require key/model/score extensions |
| Score normalization | Eight-region rank percentiles and transparent weights | Z scores preserve distance but are skew-sensitive | Direction/weight instability; traces and sensitivity |
| Low volume | Warning/category, not row deletion | Threshold filtering hides observations | 80.20% low volume; report and scenario checks |
| Power BI | Import star model with explicit DAX | DirectQuery adds dependencies/latency | Relationship/filter mismatch; three-state reconciliation |
| Tableau | Flat map-ready source and `MIN` repeated score | Related tables reduce repetition but complicate actions | Summed score/incorrect detail; dictionary and real-tile check |

## 10G. Analytical interpretation tutorial

1. Histograms answer how tile download/upload values are distributed; they show skew but not geography or cause.
2. The latency histogram/box treatment shows a long tail; high values remain observations, not automatic errors.
3. Regional boxplots compare tile distributions; different participation and tile mix limit causal comparison.
4. Weighted regional bars answer a test-influence question; they are not population-weighted experience.
5. The scatterplot tests association between tile download and latency. Pearson -0.0731 and Spearman -0.1576 are weak and noncausal.
6. The volume chart shows 80.20% low-volume tiles, directly motivating uncertainty warnings.
7. The tile map displays observed locations and values; density reflects participation and is not coverage.
8. The priority score combines relative weakness, latency, and evidence sufficiency. Rajshani remains first across four scenarios, while middle ranks move; this is a stable follow-up hypothesis, not fault detection.

Descriptive comparisons summarize the available aggregates. Generalization to residents, subscribers, operators, towers, or causal mechanisms requires a sampling design and direct network evidence not present here.

## 10H. Clean reproduction

Follow `docs/RUNBOOK.md` in order. It lists setup, commands, expected outputs, and recovery for download, schema, RAM, CRS, empty matches, duplicates, nulls, SQLite locks, weighted mismatches, score changes, BI path/filter errors, and public-publishing constraints.

## 10I. Memorize, understand, reference

### Memorize

- Mbps = kbps / 1,000.
- Grain = one quadkey per quarter.
- Weighted mean = `SUM(metric * tests) / SUM(tests)`.
- `COUNT(column)` excludes nulls; `COUNT(*)` does not.
- 15,956 tiles, 62,785 tests, weighted download 37.625394 Mbps.
- Tests/devices are not subscribers/population; tiles are not towers.

### Understand deeply

- Spatial filtering, CRS, centroid tradeoffs, grain, keys, null eligibility, weighted denominators, sampling bias, EDA interpretation, score sensitivity, BI filter context, and the boundary between observation and cause.

### Reference as needed

- Package APIs, uncommon SQL/window syntax, CRS utility calls, plotting configuration, advanced DAX/Tableau dialogs, large-data tuning, hashes, and publication settings.

## 10J. Interview and presentation

`docs/INTERVIEW_QA.md` contains every saved phase question with answers, the requested SQL/Python/statistics/Power BI/Tableau/business/architecture drill, and debugging exercises. `docs/PROJECT_PRESENTATION.md` contains a 60-second pitch, three-minute technical overview, five-minute walkthrough, management explanation, CV bullet, and portfolio summary.

## Final acceptance ledger

| Condition | Status |
|---|---|
| Source, extraction, cleaning, SQLite, SQL, EDA, scoring | Pass |
| Power BI/Tableau curated rows and formulas reconcile | Pass |
| Real tile and KPI trace generated | Pass |
| Runbook, lineage, decisions, learning, Q&A, presentation | Pass |
| Native PBIX/TWBX, genuine screenshots, interactive filters/actions | Pending manual Desktop checkpoint |
| Overall project completion | Pending until the native BI checkpoint is evidenced |
