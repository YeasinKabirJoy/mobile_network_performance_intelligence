# Mobile Network Performance Intelligence

A phased, reproducible portfolio project that investigates public Ookla mobile-network performance map tiles for Bangladesh. The project treats the data as quarterly, aggregated measurements - not cell towers, subscribers, operator results, outages, or live monitoring.

## Current status

Phase 4 - SQLite modeling and analytical SQL complete and awaiting the learner checkpoint. EDA, scoring, and dashboards are intentionally deferred.

## Phase 1 outputs

- `docs/BUSINESS_REQUIREMENTS.md` - stakeholders, decisions, scope, and answerable questions.
- `reports/SOURCE_MANIFEST.md` - source identity, access evidence, licensing, and provenance.
- `docs/DATA_DICTIONARY.md` - source fields, units, meanings, and cautions.
- `reports/DATA_QUALITY_BASELINE.md` - observed schema, counts, nulls, coordinate coverage, and representative records.
- `notebooks/01_source_review.ipynb` - reproducible source-inspection walkthrough.
- `src/inspect_source.py` - repeatable inspection and Bangladesh bounding-box coverage check.
- `docs/PROJECT_DECISIONS.md` and `docs/LEARNING_NOTES.md` - decision log and learning checkpoint.

## Setup on Windows PowerShell

```powershell
uv venv --python 3.11 .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If `uv` is unavailable, use an installed Python 3.11+ executable with `-m venv .venv`.

Download the official Q4 2024 mobile Parquet file to:

```text
data/raw/2024-10-01_performance_mobile_tiles.parquet
```

Then run:

```powershell
python -m src.inspect_source
jupyter lab notebooks/01_source_review.ipynb
```

The inspection command writes machine-readable evidence under `reports/generated/`. Raw and generated data are excluded from Git.

Run the Phase 2 extraction with:

```powershell
python -m src.extract
jupyter lab notebooks/02_geographic_extraction.ipynb
```

This creates the ignored analytical subset at `data/interim/bgd_mobile_tiles_2024_q4.parquet`, a committed audit JSON, and a geographic validation figure. PyArrow and GeoPandas handle Parquet/spatial work; SQLite is the selected database for later phases.

Run Phase 3 with:

```powershell
python -m src.clean
python -m src.validate
jupyter lab notebooks/03_data_cleaning.ipynb
```

The processed Parquet and CSV are written under `data/processed/` and excluded from Git. Their hashes, validation results, and all exclusion counts are committed under `reports/`.

Run Phase 4 with:

```powershell
python -m src.build_database
python -m src.run_sql
python -m src.reconcile
jupyter lab notebooks/04_sql_analytics.ipynb
```

The generated SQLite database remains under `data/processed/`. Named SQL results, build evidence, and Python reconciliation evidence are written under `reports/generated/`.

## Source and license

Speedtest by Ookla Global Fixed and Mobile Network Performance Maps are licensed under CC BY-NC-SA 4.0. geoBoundaries ADM1 data is separately licensed under CC0 1.0. See `reports/SOURCE_MANIFEST.md` for URLs, access dates, and attribution requirements.

## Scope guardrail

Do not infer operator performance, coverage, outages, root causes, or population experience from this dataset alone. All published findings must be reproducible from verified project artifacts and must carry appropriate sampling and aggregation caveats.
