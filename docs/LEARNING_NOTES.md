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

## Phase 5 concepts

### Understand deeply

- Mean, median, percentiles, spread, and skew describe different properties of a distribution.
- A boxplot reveals center and dispersion but can hide geographic and participation context.
- Pearson correlation summarizes linear association; Spearman correlation summarizes monotonic rank association.
- A statistically or visually unusual observation is not automatically invalid or operationally important.
- Association does not establish causation, especially with aggregated geographic data.
- Maps are powerful but can encourage coverage or population interpretations that the source cannot support.

### Memorize

- Median tile download: 27.8645 Mbps; mean: 36.0781 Mbps.
- Median idle latency: 27 ms; p95: 56 ms.
- Low-volume tiles: 12,797 of 15,956 (80.20%).
- Download/latency association is weak: Pearson -0.0731, Spearman -0.1576.
- There is only one quarter, so no trend or persistence claim is valid.

### Reference as needed

- Plot styling and Matplotlib/Seaborn parameters.
- Exact percentile APIs and color-map configuration.
- Advanced statistical tests, confidence intervals, and survey-weighting methods.

## Phase 5 interview questions

1. When is the median more informative than the mean for network-performance tiles?
2. Why can a visually strong geographic pattern still be misleading?
3. What is the difference between Pearson and Spearman correlation?
4. Why does correlation not establish the cause of weak network performance?
5. How does low test volume affect comparison and prioritization?

## Phase 5 practical exercise and checkpoint

Choose six Phase 5 figures. For each, state the business question, aggregation, reason for the chart type, one actual observation, and one limitation without reading `EDA_FINDINGS.md`.

## Phase 6 concepts

### Understand deeply

- A percentile rank describes relative position within the comparison set; it is not the percentage by which one region is better or worse.
- A z score expresses distance from the mean in standard-deviation units and can be sensitive to skew and extreme observations.
- The interquartile range (IQR) is Q3 minus Q1 and summarizes the middle half of a distribution without relying on the extremes.
- Normalization puts unlike measures on a common scale, but it does not make weights objective or remove sampling bias.
- A composite score is a documented decision rule. Its result depends on metric direction, transformation, weight, missingness, and tie policies.
- Sensitivity analysis reveals whether priorities are stable when reasonable weights change.
- A high priority score creates a hypothesis for investigation. It cannot prove a tower, operator, capacity, radio, transport, or hardware fault.

### Memorize

- Base score: `100 * (0.45 * speed weakness + 0.35 * latency weakness + 0.20 * data sufficiency)`.
- Lower speed means higher weakness; higher idle latency means higher weakness.
- Persistence is null and weighted zero because only Q4 2024 is available.
- Rank 1 is the highest comparative investigation priority, not the worst proven network.
- Rajshani remains rank 1 in all four tested weighting scenarios.

### Reference as needed

- Percentile-rank and z-score formulas.
- Alternative normalization and tie methods.
- Weight elicitation, uncertainty intervals, and multi-criteria decision analysis.
- Multi-quarter persistence definitions once additional periods are acquired.

## Phase 6 interview questions

These are preserved for the final consolidated answer with the questions from every phase:

1. Why use percentile normalization instead of combining raw Mbps and milliseconds directly?
2. How do percentile ranks, z scores, and the IQR differ?
3. Why does data sufficiency affect prioritization without representing population or subscribers?
4. What does the sensitivity analysis reveal about the stability of the ranking?
5. Why is the composite priority score a hypothesis generator rather than proof of a network fault?

## Phase 6 practical exercise and checkpoint

Recalculate the three documented top-region traces by hand. Then create one defensible alternative weighting scenario, state the decision preference it represents, compare every changed rank, and explain why the result still cannot diagnose a fault.

## Phase 7 concepts

### Understand deeply

- Power Query shapes and loads data; DAX evaluates calculations over the loaded semantic model and current filter context.
- Import mode stores a model copy in the report; DirectQuery sends queries to a supported source during interaction.
- A fact table records events or measurements at a declared grain; a dimension supplies reusable filters and labels.
- A measure is evaluated dynamically under filter context. A calculated column is stored row by row during refresh.
- `CALCULATE` modifies filter context; `DIVIDE` safely handles a zero denominator; `SUMX` evaluates an expression row by row before summing.
- A region slicer changes both numerator and denominator because it filters the tile fact before the measures evaluate.
- Incorrect relationships, bidirectional filters, implicit sums, or mismatched eligibility rules can make a polished dashboard disagree with SQLite.

### Memorize

- Model path: `DimRegion -> FactTilePerformance` and `DimRegion -> FactRegionPriority`; likewise for `DimQuarter`.
- Weighted download: `DIVIDE(SUMX(FactTilePerformance, avg_d_mbps * tests), [Tests])`.
- Default verified values: 15,956 tiles, 62,785 tests, 37.625394 Mbps weighted download.
- Dhaka: 4,420 tiles and 33.797656 Mbps weighted download.
- Rajshani: 1,582 tiles and 34.166719 Mbps weighted download.
- Import refresh begins by regenerating curated files from SQLite.

### Reference as needed

- Power BI visual-formatting controls and interaction editor.
- Data-category and geographic-role settings.
- Power Query source-path changes.
- PBIX/PBIP publication and workspace configuration.

## Phase 7 interview questions

These are preserved for the final consolidated answer:

1. What is the difference between Power Query and DAX?
2. Why use explicit measures instead of implicit aggregation for network KPIs?
3. How does filter context change a weighted KPI when a region is selected?
4. Why use two fact tables with shared dimensions instead of joining priority directly to every tile row?
5. What checks would you perform when a Power BI card disagrees with SQLite?

## Phase 7 practical exercise and checkpoint

Assemble the report page from the build guide, create the weighted-download and weighted-idle-latency measures without copying, and reconcile the All Bangladesh, Dhaka, and Rajshani selections. Explain any difference larger than display rounding before proceeding.

## Phase 8 concepts

### Understand deeply

- Dimensions identify, group, and filter marks; measures are aggregated over those groups.
- Discrete fields create headers, while continuous fields create axes and ranges.
- The Marks card controls mark type, color, size, label, detail, and tooltip.
- A calculated field encodes reusable analytical logic; its result still depends on the view's level of detail and filters.
- Context filters change Tableau's order of operations and should be used only when dependent filtering or top-N logic requires them.
- Parameters are user-controlled scalar values; sets define membership; dashboard actions connect a selection to filter or highlight behavior.
- Map selection is powerful for exploration, but geographic marks still reflect measurement participation and cannot prove coverage or causality.

### Memorize

- Tableau weighted download: `SUM([avg_d_mbps] * [tests]) / SUM([tests])`.
- One map mark = one tile-quarter record when `Tile-Quarter Key` is on Detail.
- Regional priority must use `MIN([base_score])`, not `SUM`, because it repeats on tile rows.
- Tile `1320222021021031` is a real Dhaka high-volume example with 319 tests and 28.630 Mbps download.
- Q4 2024 is the only period, so quarter comparison remains a filter-ready placeholder, not a trend.

### Reference as needed

- Shelf placement, formatting panes, and Marks card syntax.
- Context-filter order of operations.
- Parameter/set creation and dashboard action dialogs.
- TWB/TWBX packaging and Tableau Public publication controls.

## Phase 8 interview questions

These are preserved for the final consolidated answer:

1. What is the difference between a Tableau dimension and measure, and between discrete and continuous fields?
2. Why must the regional priority score use `MIN` rather than `SUM` in the flat tile source?
3. How does the selected-tile dashboard action preserve the intended grain?
4. Why is a map of observed tile values not a coverage map?
5. How would you diagnose a Tableau weighted KPI that disagrees with SQLite and Power BI?

## Phase 8 practical exercise and checkpoint

Build the Tile Map and Selected Tile Details worksheets, configure the map-selection filter action, and select quadkey `1320222021021031`. Verify every displayed value and independently reproduce its 9,132.97 Mbps-tests numerator contribution before building the remaining sheets.

## Phase 9 concepts

### Understand deeply

- A verifiable observation is directly reproduced from defined data and calculations; a hypothesis proposes what might explain it; a recommendation specifies a next action under uncertainty.
- Reconciliation requires identical grain, filters, units, eligibility rules, numerator, denominator, and rounding—not merely similar-looking values.
- A lineage inventory explains where every output came from and which downstream results must be rebuilt after an upstream change.
- Portfolio quality depends on honest limitations and reproducibility as much as visual polish.
- Import/export-layer agreement cannot prove that a dashboard visual has correct relationships, filters, interactions, or calculations.

### Memorize

- Verified default scope: 15,956 tiles, 62,785 tests, 29,693 summed tile device counts.
- Weighted KPIs: 37.625394 Mbps download, 16.039675 Mbps upload, 31.137915 ms idle latency.
- Low-volume share: 12,797 / 15,956 = 80.20%.
- Automated numeric tolerance: `1e-9`.
- Observed weak measurement is evidence for follow-up, not causal proof.

### Reference as needed

- Exact file hashes and generated evidence timestamps.
- Detailed run commands and troubleshooting steps, completed in Phase 10.
- License text and publication-platform settings.
- Full cross-tool comparison tables.

## Phase 9 interview questions

These are preserved for the final consolidated answer:

1. How do you distinguish an observation, hypothesis, recommendation, and causal conclusion?
2. What must match before two tools can be said to reconcile?
3. Why does import-layer reconciliation not prove a dashboard is correctly configured?
4. How does data lineage help diagnose a changed result after refresh?
5. Which limitation most affects regional interpretation in this project, and how would you reduce it?

## Phase 9 practical exercise and checkpoint

Choose three business-summary findings. For each, locate the generated evidence, reproduce the calculation, state the grain and denominator, identify one unsupported causal interpretation, and propose one additional dataset needed for a stronger decision.

## Phase 10 final learning checkpoint

### Understand deeply

- A workflow explanation must connect business decisions, data lineage, code, calculations, visuals, limitations, and reproduction—not merely list files.
- A record trace proves row-level lineage; a KPI trace proves calculation/denominator consistency. Both are needed.
- Tool agreement is meaningful only under identical filter and eligibility conditions.
- Honest incomplete status is stronger evidence of engineering judgment than fabricated dashboard completion.

### Memorize

- Real tile: `1320222021021031`, Dhaka, 28.630 Mbps, 319 tests.
- Tile numerator contribution: 9,132.97 Mbps-tests.
- Dhaka KPI: 863,192.131 / 25,540 = 33.797655873 Mbps.
- Final documentation locations: workflow, tile trace, KPI trace, runbook, interview Q&A, presentation.

### Reference as needed

- The seven-item file tour and change-impact matrix.
- Full troubleshooting paths.
- Fifty interview questions and presentation scripts.

## Final practical exercise

Without notes, deliver the five-minute walkthrough. Then reproduce the real tile lookup and Dhaka weighted KPI in Python and SQLite. Finally, assemble each native BI dashboard, demonstrate the same tile/filter behavior, record genuine screenshots, and update the acceptance ledger from pending to pass only after exact reconciliation.
