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

## D-009 - Phase 5 descriptive-analysis policy

- Decision: report distribution statistics, tile-level charts, and explicitly labeled test-weighted regional KPIs side by side.
- Reason: tile means, medians, and weighted reconstructions answer different questions and should not be blended.
- Correlation: report both Pearson and rank-based Spearman values as descriptive association only.
- Maps: display actual tile centroids; cap only the color scale at the 95th percentile so extreme values remain in the data but do not flatten visual contrast.
- Time limitation: do not manufacture a trend from a single quarter.
- Outliers: retain and show the full distribution, with a second latency panel through the 99th percentile for readable central detail.

## D-010 - Explainable investigation-priority score

- Decision: rank the eight ADM1 regions with transparent 0-1 rank-percentile components and a 0-100 weighted composite.
- Base weights: speed weakness 45%, idle-latency weakness 35%, data sufficiency 20%, persistence 0%.
- Direction: lower download/upload speeds increase weakness; higher idle latency and stronger evidence volume increase their respective components.
- Speed component: the equal-weight average of download-weakness and upload-weakness percentiles.
- Sufficiency component: the equal-weight average of log test-volume and high-volume-tile-share percentiles. It increases confidence in where to investigate; it is not population coverage.
- Persistence: unavailable for a single quarter, so it remains null and receives zero weight rather than being imputed.
- Threshold policy: no performance pass/fail cutoff is invented. Low/medium/high tile-volume thresholds remain the Phase 3 disclosure labels only.
- Ties: component percentiles use average ranks; scenario ranks use the shared minimum rank, with ADM1 ISO only as a deterministic display order.
- Missingness: a region must have valid speed, idle latency, and evidence-volume inputs. Nullable loaded latency is disclosed in quality notes but is not silently substituted into the score.
- Sensitivity: compare base weights with speed-emphasis, latency-emphasis, and lower-volume-influence scenarios.
- Interpretation: priority indicates where comparative evidence supports follow-up. It is neither a fault diagnosis nor a probability of failure.

## D-011 - Power BI import model and dashboard handoff

- Decision: generate four curated CSV imports from the SQLite fact/dimension model and the Phase 6 priority output.
- Model: separate tile-performance and region-priority facts filtered by shared region and quarter dimensions; no direct fact-to-fact relationship.
- Filter direction: single direction from each dimension to each fact to avoid ambiguous propagation.
- Storage: Import mode because the validated dataset is small, portable, and refreshed deliberately from the reproducible pipeline.
- Measures: use explicit DAX with `SUMX`, `DIVIDE`, and metric-eligible denominators; prohibit implicit performance aggregations.
- Devices: display the sum of tile-level device counts with a warning that it is not globally deduplicated and does not represent subscribers or population.
- Map: plot measurement tile coordinates and values, never label the display as coverage.
- Reconciliation: require the default view plus Dhaka and Rajshani filters to reproduce SQLite before dashboard acceptance.
- Environment limitation: native Power BI window attachment was unavailable, so this phase delivers verified import/model/DAX/build assets and a clearly labeled static build reference, not a fabricated `.pbix` or screenshot.

## D-012 - Tableau flat explorer model and action design

- Decision: provide one flat tile-quarter Tableau source with repeated region-quarter priority attributes.
- Reason: a single, map-ready source keeps geographic marks, distributions, regional comparisons, and selected-tile details in one filter domain.
- Aggregation safeguard: region priority uses `MIN`, never `SUM`, because the regional value repeats on every tile row.
- Geography: explicit latitude/longitude roles on tile centroids; marks are labeled measurement tiles rather than coverage.
- Calculations: weighted measures reproduce SQLite/Power BI numerator and denominator rules, including nullable-metric eligibility.
- Time: retain the quarter filter but do not manufacture a trend or line chart from one quarter.
- Actions: tile selection filters details; regional selections filter explorer sheets; region highlight links map and comparisons.
- Color: use sequential performance color and disclose percentile clipping if used for display; extreme records remain in the source.
- Publication: Tableau Public is optional only after license/attribution and public-data exposure review; local CSV sources do not refresh automatically there.
- Environment limitation: Tableau Desktop is installed but native window attachment was unavailable, so the verified handoff does not claim a `.twb`, `.twbx`, or Tableau screenshot.

## D-013 - Phase 9 assurance and claim-control boundary

- Decision: treat every headline number as a testable claim backed by generated JSON and cross-tool reconciliation.
- Required layers: Python/SQLite, Power BI curated-import recalculation/SQLite, and Tableau flat-export recalculation/SQLite.
- Tolerance: absolute difference `1e-9` for automated numeric comparisons; display rounding is documented separately.
- Dashboard boundary: import/export reconciliation proves input rows and formulas, not native visual configuration or interactions.
- Documentation: separate observed findings, hypotheses, recommendations, and limitations so business relevance does not imply causal certainty.
- Completion: Phase 9 can pass automated assurance while the overall project remains incomplete until Phase 10 and native BI checkpoints are handled.

## D-014 - Final completion ledger

- Decision: separate completion of the reproducible analytics/documentation workflow from native dashboard acceptance.
- Evidence complete: source-to-output architecture, seven-item file tour, real tile trace, KPI trace, decisions, runbook, learning model, interview drill, and presentation scripts.
- Consequence: Step 10 documentation is complete and verified.
- Validation: `src.final_trace`, `src.assure`, unit tests, notebook error scan, compile check, and diff check.

## D-015 - Native Power BI and Tableau Desktop dashboard completion

- Decision: build, verify, and document native Desktop workbooks and interactive screenshots.
- Power BI: native workbook `powerBI/dashboard.pbix` constructed using the 4 curated CSV tables, 1-to-many Star Schema, and explicit DAX measures; verified against benchmark reconciliation. Native screenshot captured and referenced.
- Tableau: native workbook `tableau/dashboard.twb` constructed with 4 core views (`Tile_Map`, `Region_Comparison`, `Investigation_Priority`, `Latency_Distribution`) on `Geographic_Explorer` dashboard; verified against benchmark reconciliation. Native screenshot captured and referenced.
- Status: both manual desktop checkpoints are completed and verified; `src.assure` and portfolio assets updated.
