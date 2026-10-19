# Project Decisions

## D-001 - Initial period and service

- Decision: use Q4 2024 and the mobile layer.
- Reason: the project specification identifies this as the canonical starting source.
- Tradeoff: a single period cannot support persistence or quarter-over-quarter claims.
- Validation: verify the exact remote object and actual local schema before downstream design.

## D-002 - Parquet-first analysis

- Decision: retain and inspect the official Parquet file rather than converting it to CSV.
- Reason: Parquet preserves types, supports projection, and enables efficient analytical scans.
- Alternative: Shapefile ZIP, retained as a documented fallback.
- Failure scenario: access or schema changes; record the blocker and use an official supported alternative.

## D-003 - Coverage evidence in Phase 1

- Decision: use a conservative bounding box to reduce candidates, then test centroids against the official ADM1 polygons to verify country coverage.
- Reason: it proves actual Bangladesh observations exist without producing the audited extraction dataset.
- Limitation: the check uses centroids and does not settle border-tile policy or validate every geometry.
- Phase 2 requirement: use verified boundaries, CRS checks, and an explicitly chosen spatial rule.

## D-004 - Raw-data immutability

- Decision: raw downloads are never edited and are excluded from Git.
- Validation: record byte size and SHA-256 digest in the source manifest.

## D-005 - Interpretation boundary

- Decision: describe results as observed tile-level performance patterns.
- Prohibited inference: operator faults, coverage, outages, subscriber experience, or causal explanations from this source alone.

## D-006 - SQLite analytical database

- Decision: use SQLite instead of DuckDB for database-backed work from Phase 2 onward.
- Reason: explicit learner preference recorded at the Phase 2 checkpoint.
- Consequence: Parquet projection and geographic filtering remain the responsibility of PyArrow/GeoPandas; curated rows will be loaded into SQLite in later phases.
- Tradeoff: SQLite does not natively scan Parquet and has fewer analytical SQL features, so ingestion and some percentile/statistical calculations will require explicit Python support or carefully documented SQL alternatives.

## D-007 - Geographic assignment rule

- Decision: pre-filter by bounding box, convert source centroids to EPSG:4326 points, and assign ADM1 using centroid intersection with the official polygons.
- Reason: one deterministic reporting region per tile is easier to audit and avoids duplicating tiles that cross boundaries.
- Border behavior: a centroid exactly on more than one ADM1 boundary is flagged as ambiguous and assigned deterministically by ascending `shapeISO`.
- Tradeoff: a tile polygon can overlap a region even when its centroid lies elsewhere; Phase 2 reports this limitation rather than silently using intersection area.

## D-008 - Cleaning, null, and low-volume policy

- Decision: reject structurally invalid rows but preserve zero or unusually weak performance values when counts and types are valid.
- Reason: weak network measurements may be analytically important; extremeness alone is not proof of corruption.
- Loaded latency: retain nulls and add `loaded_latency_complete`; never impute zero.
- Speed units: retain source kbps and derive Mbps by division by 1,000.
- Evidence-volume labels: low = 1-4 tests, medium = 5-19, high = 20+. These labels disclose uncertainty and do not remove rows.
- Grain: enforce unique `(quadkey, period_start)` records.
