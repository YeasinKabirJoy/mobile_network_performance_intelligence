# Learning Notes

## Phase 1 concepts

### Understand deeply

- The source row is a quarterly aggregate for a map tile, not a raw speed test, tower, user, or operator.
- Uneven participation creates sampling bias. More tests can improve stability but do not make the sample population-representative.
- A regional mean of tile means answers a different question from a test-weighted regional mean.
- CRS describes how coordinates map to Earth. The source geometry is represented in EPSG:4326, while the tiling system is based on Web Mercator.
- Geographic bounding boxes are efficient candidate filters but do not implement precise country or administrative membership.
- Apparent weak performance is an observation to investigate, not proof of a fault or its cause.

### Memorize

- `Mbps = kbps / 1,000`
- Q4 2024 covers 2024-10-01 through 2024-12-31.
- Lower latency is generally preferable.
- `tests` is not subscribers; `devices` is not population.
- Intended grain: one tile per quarter.

### Reference as needed

- Package syntax and environment setup.
- WKT parsing and CRS transformation APIs.
- Quadkey conversion utilities.
- Precise geoBoundary file metadata.

## Interview questions

1. **Why use Parquet instead of CSV?** It preserves typed columnar storage and permits selective, compressed scans of large datasets.
2. **Why can an unweighted regional average be misleading?** Every tile receives equal influence even when their contributing test counts differ substantially.
3. **What does a quadkey identify?** A tile in a hierarchical web-map grid; it is not a cell tower or measurement ID.
4. **Why does a Bangladesh bounding box not complete extraction?** The rectangle includes areas outside the country and cannot resolve borders or ADM1 membership.
5. **Can weak tile measurements prove a network fault?** No. They are aggregated observations affected by participation and context, and require operational corroboration.

## Practical exercise and checkpoint

Without notes, explain the dataset grain, the units of all performance metrics, the difference between tests and devices, two forms of sampling bias, and why Phase 1 uses a bounding box only for feasibility. Then inspect the generated JSON and identify one result that is evidence and one conclusion that would overreach the evidence.

## Phase 2 concepts

### Understand deeply

- Coordinates have meaning only with a CRS. Both source centroids and selected boundaries are handled in EPSG:4326.
- A bounding box cheaply rejects most global rows, but its rectangle contains India, Myanmar, water, and other non-Bangladesh locations.
- The precise test assigns each tile by its centroid. This produces one reporting region but can differ from tile-polygon intersection near borders.
- A spatial join attaches boundary attributes to geometries satisfying a spatial predicate; it is not an ordinary equality join.
- Dense clusters reflect measurement participation as well as network and population patterns, so the map is not a coverage map.

### Memorize

- CRS mismatch symptoms: misplaced, missing, or globally displaced geometries.
- Fast sequence: column projection -> bbox candidates -> precise spatial predicate -> assignment audit.
- Selected rule: centroid intersects ADM1; deterministic ISO ordering for an exact boundary tie.
- Phase 2 retained 15,956 of 49,213 bbox candidates across all eight boundary features.

### Reference as needed

- GeoPandas spatial-join syntax.
- GeoParquet metadata details.
- Geometry repair utilities and projected-area calculations.

## Phase 2 interview questions

1. **Why use a bounding box before a spatial join?** It removes most global rows with cheap numeric comparisons, reducing geometry work.
2. **Why is the bounding box insufficient?** It is rectangular and therefore includes locations outside Bangladesh.
3. **Why choose centroid assignment?** It gives one deterministic regional owner per tile and prevents duplicate aggregation, at the cost of simplifying cross-border tiles.
4. **What happens when coordinate reference systems differ?** Spatial predicates compare incompatible coordinate spaces and can return empty or incorrect matches.
5. **Does the retained-point map demonstrate mobile coverage?** No. It shows locations of aggregated measurements that met the source participation rules.

## Phase 2 practical exercise and checkpoint

Pick one retained quadkey from the interim data. Confirm its longitude and latitude satisfy the bbox, find its ADM1 assignment, and explain why the centroid rule assigns it there. Then explain what could change if polygon-overlap assignment were used instead.

## Phase 3 concepts

### Understand deeply

- Null and zero are different: null means unavailable; zero is an observed value that may be valid or suspicious.
- Type coercion can reveal invalid text values, but silently coercing without an audit would hide data loss.
- Duplicate keys violate the declared tile-quarter grain even if every other field appears plausible.
- Removing slow or high-latency observations as "outliers" can erase the phenomenon the project is intended to investigate.
- Imputation changes distributions and denominators. Loaded-latency nulls remain null and are disclosed through a completeness flag.
- Low measurement volume increases uncertainty. The volume category is a warning, not a quality-based deletion.

### Memorize

- `avg_d_mbps = avg_d_kbps / 1,000`
- `avg_u_mbps = avg_u_kbps / 1,000`
- Grain key: `(quadkey, period_start)`
- Low volume: 1-4 tests; medium: 5-19; high: 20+.
- Missing loaded latency is not zero latency.

### Reference as needed

- Pandas nullable integer types.
- GeoParquet metadata implementation.
- CSV serialization details and hash commands.

## Phase 3 interview questions

1. **Why preserve a zero or very slow measurement?** Extremeness is not sufficient evidence of invalidity and may represent the condition being investigated.
2. **What is the difference between null and zero?** Null is missing or unavailable; zero is a present numeric value with domain meaning.
3. **Why enforce a composite tile-period key?** The same quadkey can legitimately recur across quarters, but only once within a quarter at the intended grain.
4. **How can dropping null loaded-latency rows bias analysis?** It changes the eligible population and may systematically remove tests from particular clients or locations.
5. **Why keep both kbps and Mbps fields?** Source values preserve lineage while Mbps fields give consistent reporting units and easy conversion verification.

## Phase 3 practical exercise and checkpoint

Change `low_volume_max_tests` from 4 to 5 in a temporary branch or local experiment, rerun cleaning, and explain which rows move from medium to low. Confirm that the row count and performance values do not change.

## Phase 4 concepts

### Understand deeply

- Table grain determines what a row means and which keys must be unique.
- A fact table stores measurements at a declared grain; a dimension provides reusable descriptive attributes.
- `GROUP BY` changes the output grain, while `WHERE` changes the eligible population before aggregation.
- A weighted and unweighted mean can both be correct while answering different questions.
- The denominator for a nullable metric must include only rows eligible for that metric.
- CTEs make multi-step logic auditable; window functions add rankings or partitions without collapsing rows.
- SQLite is reliable for this local analytical scale but does not natively scan Parquet or provide every warehouse percentile function.

### Memorize

- Weighted mean: `SUM(metric * weight) / SUM(weight)`.
- SQLite real division: ensure at least one operand is real, such as multiplication by `1.0`.
- Grain key: `(quadkey, period_start)`.
- `COUNT(column)` excludes nulls; `COUNT(*)` counts rows.
- Loaded-latency nulls must be excluded from both numerator and denominator.

### Reference as needed

- SQLite window-function syntax.
- `EXPLAIN QUERY PLAN` and index tuning.
- Python `sqlite3` connection options and transaction handling.

## Phase 4 interview questions

Fifteen SQL analyses and the following checkpoint questions are preserved for the final consolidated answer:

1. Why do weighted and unweighted download means differ?
2. How do `WHERE` and `HAVING` affect an aggregation differently?
3. Why is `COUNT(*)` inappropriate for the denominator of nullable loaded latency?
4. When should a CTE be preferred over a deeply nested query?
5. How does a window-function ranking differ from grouped aggregation?

## Phase 4 practical exercise and checkpoint

Recreate five core queries without copying the project SQL: dataset totals, regional test volume, test-weighted download by region, loaded-latency eligibility, and regional download ranking. Compare the outputs with the committed generated CSVs and explain every denominator.
