# Data Lineage Inventory

## End-to-end flow

```text
Official Ookla Q4 2024 Parquet + geoBoundaries ADM1 GeoJSON
  -> source inspection and checksums
  -> bbox candidates + centroid-in-polygon assignment
  -> cleaned tile-quarter GeoParquet/CSV
  -> SQLite fact_tile_performance + dim_region
  -> named SQL results + Python reconciliation
  -> EDA summaries and figures
  -> regional investigation-priority dataset
  -> Power BI curated star-model CSVs
  -> Tableau flat geographic-explorer CSV
  -> business findings and Phase 9 assurance audit
```

## Inventory

| Stage | Primary inputs | Transformation | Primary outputs | Validation |
|---|---|---|---|---|
| Source | Official Parquet and boundary metadata/GeoJSON | Schema, counts, nulls, URL and checksum inspection | Source manifest and baseline | Local/remote byte match, schema and Bangladesh coverage |
| Geography | Global Parquet + ADM1 polygons | Project columns, bbox pre-filter, centroid spatial assignment | Bangladesh interim GeoParquet | Counts, eight regions, unmatched/tie audit, map |
| Cleaning | Interim tile rows | Type/range/key checks, Mbps derivation, volume labels | Clean GeoParquet/CSV | Exclusion counts, hashes, 15,956 output rows |
| Database | Clean GeoParquet + SQL schema | Load SQLite fact and region dimension | `network_performance.sqlite` | PK/FK checks, database audit |
| SQL | SQLite tables | 15 named aggregations, windows, CTEs, CASE and joins | Generated CSV results | Eight Python/SQLite comparisons pass |
| EDA | Clean GeoParquet | Distributions, correlations, regional weighted metrics, map | Eight figures + JSON + findings | Automated summary test and explicit caveats |
| Scoring | Clean tile data | ADM1 aggregation, percentile components, weights, scenarios | Priority CSV/Parquet + audit + figures | Three traces, four scenarios, bounded-score tests |
| Power BI | SQLite + priority dataset | Four curated imports and explicit DAX specification | Import CSVs + build guide | 18 import-layer comparisons across three filters |
| Tableau | SQLite + priority dataset | Flat tile explorer, calculated-field specification | Explorer CSV + dictionary + build guide | 18 export-layer comparisons and selected-tile trace |
| Assurance | All committed reports and generated evidence | Required-artifact, claim and reconciliation checks | Business summary + assurance JSON | Automated Phase 9 pass, native BI checkpoints disclosed |

## Change impact

- Source schema changes can break inspection, extraction, cleaning, SQLite loading, and every downstream artifact.
- Boundary or centroid-rule changes alter regional membership and therefore SQL, EDA, score, and dashboard values.
- Cleaning threshold changes alter quality labels and dashboard warnings even when rows are retained.
- Grain changes invalidate uniqueness, counts, relationships, and weighted denominators.
- Metric eligibility or weighting changes must be updated identically in Python, SQLite, DAX, Tableau, reports, and reconciliation tests.
- Additional quarters enable time comparison and persistence but require unique region-quarter scores and tested dashboard filters.
