# Interview Questions, Model Answers, and Debugging Drills

Try each question before reading its answer. The phase questions below include every checkpoint preserved during implementation.

## Phase 1 - source and framing

1. **Why does a row represent a quarterly map tile rather than a tower or individual test?** The source publishes one record per web-map tile for a quarter, with aggregate means and contributing counts. It contains tile geometry/quadkey but no site identifier or raw-test timestamp, so tower/test interpretations would invent grain.
2. **Why can `tests` and `devices` not represent subscribers or population?** Tests count contributing measurements and devices count unique devices only within the published aggregation. Participation is voluntary and uneven; one person/device can test repeatedly or across tiles, and nonparticipants are absent.
3. **Why is `Mbps = kbps / 1,000`?** Network throughput uses decimal SI prefixes: one megabit equals 1,000 kilobits. Dividing 28,630 kbps by 1,000 gives 28.630 Mbps; 1,024 is a binary-storage convention, not this unit definition.
4. **Why is a bounding box only a fast candidate filter?** A box uses cheap numeric coordinate comparisons, but its rectangle includes neighboring countries and water. Precise country/ADM1 membership needs a spatial predicate against verified polygons.
5. **Why do weak tile measurements suggest investigation but not prove a fault?** Aggregation, devices, demand, time, radio conditions, participation, and missing operator/site context can all affect a tile mean. Direct telemetry and field evidence are required for fault diagnosis.
6. **Why use Parquet instead of CSV?** Parquet preserves types, compresses columnar data, and supports projection and predicate-efficient scans; CSV requires parsing every row and carries weaker type metadata.
7. **Why can an unweighted regional average mislead?** It gives a one-test tile the same influence as a 319-test tile. It is valid for the typical tile, but not for a reconstruction weighted by observed tests.
8. **What does a quadkey identify?** A position in a hierarchical web-map tiling grid, not a cell tower, user, or individual measurement.

## Phase 2 - geographic extraction

1. **Why use a bounding box before a spatial join?** It removes most global records with numeric comparisons, reducing geometry construction and predicate cost.
2. **Why is the box insufficient?** Rectangles do not follow Bangladesh's border or ADM1 shapes and retain 33,257 candidates outside the selected polygons.
3. **Why choose centroid assignment?** It creates one deterministic regional owner and avoids duplicated cross-border tiles. The tradeoff is that a tile can overlap another region more than the one containing its centroid.
4. **What happens when coordinate reference systems differ?** Coordinates are compared in incompatible spaces, producing misplaced, empty, or incorrect matches. Both inputs must be transformed to a common CRS.
5. **Does the retained-point map demonstrate coverage?** No. It maps locations of qualifying aggregated measurements; absence can reflect participation, not lack of service.

## Phase 3 - cleaning and validation

1. **Why preserve zero or very slow measurements?** Extremeness alone is not invalidity and may be the phenomenon under study. Remove only when a documented structural/domain rule fails.
2. **What is the difference between null and zero?** Null means unavailable/unknown; zero is a present value. Replacing null latency with zero falsely creates perfect latency.
3. **Why enforce `(quadkey, period_start)`?** A tile may recur in different quarters but should appear once within one quarter at the declared grain.
4. **How can dropping null loaded-latency rows bias analysis?** Missingness may be associated with client, place, or conditions; dropping changes the population and can shift regional comparisons.
5. **Why keep kbps and Mbps fields?** Raw kbps preserves lineage and enables conversion audits; Mbps supports consistent reporting and BI use.

## Phase 4 - SQLite and SQL

1. **Why do weighted and unweighted means differ?** Unweighted `AVG` gives each tile equal influence; weighted aggregation gives influence proportional to tests. They answer typical-tile versus test-weighted reconstruction questions.
2. **How do `WHERE` and `HAVING` differ?** `WHERE` filters input rows before grouping; `HAVING` filters completed groups using aggregate conditions.
3. **Why is `COUNT(*)` wrong for nullable loaded-latency eligibility?** It includes rows whose metric is missing. Numerator and denominator must include only rows where the metric exists.
4. **When prefer a CTE over a deeply nested query?** When named stages clarify eligibility, aggregation, ranking, or reuse. It improves auditability; it is not automatically faster.
5. **How does window ranking differ from grouped aggregation?** `GROUP BY` collapses rows to groups; a window function calculates across a partition while retaining its input row grain.

## Phase 5 - EDA and statistics

1. **When is the median more informative than the mean?** With the strongly right-skewed tile distribution, the median better describes a central tile without being pulled by extreme high values.
2. **Why can a strong-looking geographic pattern mislead?** Tile density and values reflect participation, device mix, time, and aggregation as well as networks; visual clusters are not coverage or cause.
3. **Pearson versus Spearman?** Pearson measures linear association of values; Spearman measures monotonic association of ranks and is less driven by scale/extremes.
4. **Why does correlation not establish cause?** It lacks random assignment, temporal ordering, confounder control, and mechanism. Aggregated association can also suffer ecological fallacy.
5. **How does low test volume affect comparison?** It increases instability and makes tile means more sensitive to a few observations. It should trigger warnings/sensitivity checks, not automatic deletion.

## Phase 6 - scoring

1. **Why normalize instead of combining raw Mbps and milliseconds?** Raw units and scales are incompatible; normalization puts components on a comparable range before weighting.
2. **How do percentile ranks, z scores, and IQR differ?** Percentiles express relative order, z scores express standard deviations from the mean, and IQR is Q3-Q1 for the middle 50%. Percentiles lose distance; z scores are skew-sensitive; IQR is robust spread.
3. **Why can sufficiency affect priority without representing population?** It expresses confidence from observed measurement volume/high-volume tiles. It says evidence is stronger, not that more people live there.
4. **What does sensitivity reveal?** Rajshani stays first, but middle ranks move when speed versus latency preference changes. Stable and unstable decisions become visible.
5. **Why is the score a hypothesis generator?** It combines comparative public measures under subjective weights and lacks causal/site/operator evidence; it prioritizes follow-up rather than diagnosing failure.

## Phase 7 - Power BI

1. **Power Query versus DAX?** Power Query connects, cleans, and reshapes before load; DAX evaluates model calculations under filter context after load.
2. **Why explicit measures?** They encode numerator, denominator, null eligibility, and formatting consistently. Implicit sums can silently answer the wrong question.
3. **How does filter context change a weighted KPI?** A region slicer filters fact rows first, so both `SUMX(metric*tests)` and `SUM(tests)` recompute for that region.
4. **Why two fact tables with shared dimensions?** Tile performance and region priority have different grains. Shared dimensions filter both without repeating/joining the score into every tile or creating fact-to-fact ambiguity.
5. **What if a card disagrees with SQLite?** Check source refresh/path, data types, relationships/direction, slicers, implicit aggregation, DAX formula, null eligibility, and rounding—in that order.

## Phase 8 - Tableau

1. **Dimension/measure and discrete/continuous?** Dimensions group/filter marks; measures aggregate. Discrete fields create headers; continuous fields create axes/ranges.
2. **Why `MIN(base_score)`, not `SUM`?** The flat source repeats one regional score on every tile; summing multiplies it by tile count. `MIN` returns the single repeated value.
3. **How does selected-tile action preserve grain?** `Tile-Quarter Key` on Detail creates one mark per tile-quarter, and the filter action passes that exact key to the detail sheet.
4. **Why is the map not coverage?** It displays observed public measurements and participation; missing marks do not prove missing service.
5. **How diagnose a Tableau mismatch?** Match filters and data source, inspect aggregation/LOD, use exact calculated field, check duplicated regional attributes, null eligibility, context filters, and extract refresh.

## Phase 9 - assurance

1. **Observation, hypothesis, recommendation, causality?** Observation is reproduced data; hypothesis is a possible explanation; recommendation is an action to gather evidence or manage risk; causality requires a credible design/mechanism beyond association.
2. **What must match for reconciliation?** Grain, source rows, filters, units, metric eligibility, numerator, denominator, aggregation, and rounding.
3. **Why does import-layer agreement not prove a dashboard?** Visual relationships, filters, interactions, and native formulas can still be configured incorrectly.
4. **How does lineage diagnose changed results?** It identifies the earliest changed input/rule and every dependent artifact that must be rebuilt and compared.
5. **Most important limitation and mitigation?** Uneven participation/low volume strongly limits regional interpretation. Add repeated periods, uncertainty analysis, structured sampling, population/demand context, and direct network telemetry.

# Required interview drill

## 10 SQL questions

1. **What is the logical order of a grouped query?** `FROM/JOIN`, `WHERE`, `GROUP BY`, aggregates, `HAVING`, window/select expressions, `ORDER BY`, `LIMIT` conceptually.
2. **Write weighted download.** `SUM(avg_d_mbps * tests) / NULLIF(SUM(tests) * 1.0, 0)`.
3. **Why `NULLIF`?** It converts a zero denominator to null and avoids division-by-zero failure.
4. **`COUNT(*)` versus `COUNT(column)`?** The first counts rows; the second counts non-null values in that column.
5. **What does a foreign key protect?** Every fact region must have a valid dimension region, preventing orphan labels.
6. **Why index `(adm1_iso, quarter_label)`?** It supports common regional/quarter filters and grouping access, with write/storage tradeoffs.
7. **How rank regions without collapsing them further?** Aggregate in a CTE, then `RANK() OVER (ORDER BY metric DESC)`.
8. **`ROW_NUMBER`, `RANK`, `DENSE_RANK`?** Row number forces unique sequence; rank shares ties with gaps; dense rank shares ties without gaps.
9. **How find duplicates at grain?** `GROUP BY quadkey, period_start HAVING COUNT(*) > 1`.
10. **Why SQLite real division matters?** Integer operands can produce integer behavior in some expressions; multiplying by `1.0` makes intent explicit.

## 10 Python/Pandas questions

1. **Why project Parquet columns?** It reduces I/O and memory.
2. **How calculate weighted mean safely?** Validate nonnegative weights, filter eligible metrics, compute `(metric*weight).sum()/weight.sum()`, guard zero denominator.
3. **Why nullable dtypes?** They preserve missingness without coercing whole-number fields to misleading ordinary floats or sentinel values.
4. **How detect composite duplicates?** `df.duplicated(['quadkey','period_start'], keep=False)`.
5. **Why vectorization?** Column operations are clearer and faster than Python row loops for large frames.
6. **What does `merge(validate='many_to_one')` add?** It asserts expected relationship cardinality and catches duplicate dimension keys.
7. **How preserve reproducibility?** Fixed source/checksums, explicit configuration, pure-ish functions, generated audits, deterministic sorting/ties, tests.
8. **Why use both Parquet and CSV?** Parquet for typed efficient analytics; CSV for broad BI interoperability and inspectability.
9. **How avoid chained-assignment ambiguity?** Select/copy explicitly and assign with `.loc` or direct column operations.
10. **How test a transformation?** Use small known inputs including null, zero, invalid, boundary, and duplicate cases, then assert exact outputs/audits.

## 10 statistics/EDA questions

1. **Mean versus median?** Mean uses all magnitudes and is outlier-sensitive; median is the 50th percentile and robust to extreme tails.
2. **What is skew?** Asymmetry; positive skew has a long right tail and often mean above median.
3. **What is a percentile?** The value below which a stated percentage of observations fall.
4. **What does a boxplot show?** Median, quartiles, IQR-based whiskers/outliers; not sample representativeness or cause.
5. **Why show sample volume?** Precision/stability and participation differ; performance without evidence volume can mislead.
6. **Correlation near zero means no relationship?** No strong linear/monotonic association by that summary; nonlinear/subgroup relationships may still exist.
7. **What is ecological fallacy?** Inferring individual behavior from group aggregates.
8. **Why not delete outliers automatically?** Extreme network observations may be real and operationally important; validate structure before excluding.
9. **What is sensitivity analysis?** Recompute decisions under plausible assumptions/weights to see what remains stable.
10. **Can this sample estimate population experience?** Not defensibly without sampling/coverage weights and a defined target population.

## 5 Power BI questions

1. **Measure versus calculated column?** Measure evaluates at query time under filter context; column is stored per row at refresh.
2. **What does `CALCULATE` do?** Evaluates an expression in modified filter context.
3. **Why `DIVIDE`?** Safe alternate result for zero/blank denominator and clearer intent.
4. **Import versus DirectQuery?** Import stores compressed data and is fast/portable; DirectQuery queries the source live with capability/performance dependencies.
5. **Why single-direction relationships?** They give predictable dimension-to-fact propagation and reduce ambiguity/cycles.

## 5 Tableau questions

1. **What is the level of detail of a mark?** The unique combination of dimensions on the view/Marks card.
2. **What does a context filter change?** It creates an earlier filtered subset used by dependent filters/top-N/table calculations.
3. **Parameter versus filter?** A parameter is an independent user value; a filter selects data members/rows.
4. **Filter versus highlight action?** Filter removes nonmatching marks from targets; highlight keeps them visible but emphasizes matches.
5. **Why package as TWBX?** It bundles the workbook and local data resources for portable opening; contents may be readable and need publication review.

## 5 business questions

1. **What decision does the score support?** Where to request deeper investigation first under transparent priorities.
2. **What should management not do?** Declare faults, rank operators, infer coverage, or approve site remediation from public tile aggregates alone.
3. **Why is Rajshani a recommendation?** Rank 1 is stable across scenarios and latency is comparatively high, but low-volume share demands corroboration.
4. **What is the most actionable data-quality message?** 80.20% of tiles have only 1-4 tests, so evidence strength must accompany performance.
5. **What additional data has highest value?** Multiple quarters plus operator/site/traffic/incident/radio/field evidence aligned in space and time.

## 5 architecture/workflow questions

1. **Why linear phases?** Each stage creates an auditable contract and prevents downstream polish from hiding upstream errors.
2. **Why keep raw immutable?** It preserves provenance, enables reprocessing, and distinguishes source facts from transformations.
3. **Why SQLite here?** Learner preference, portability, sufficient scale, strong relational constraints; tradeoff is no native Parquet scan/advanced analytics.
4. **What is the highest-risk dependency?** Geographic assignment and grain/denominator rules because they affect every regional result.
5. **How do tests and audits complement each other?** Tests validate behavior on known cases; audits record what happened on the real run.

# Debugging exercises

## Wrong denominator

**Symptom:** weighted loaded latency is much lower after a refresh. **Injected bug:** denominator uses all tests while numerator excludes null latency. **Diagnosis:** compare eligible-row/test counts and rewrite both numerator and denominator with the same non-null predicate.

## Wrong CRS

**Symptom:** no Bangladesh matches or points plot in an impossible location. **Injected bug:** boundaries are projected while centroids are treated as EPSG:4326. **Diagnosis:** print CRS/extents, transform one dataset, plot a small overlay, rerun assignment audit.

## Null loaded latency

**Symptom:** a zero spike appears in loaded-latency distribution. **Injected bug:** `fillna(0)`. **Diagnosis:** compare source null count and zero count, restore nulls, recompute metric-eligible denominators.

## Dashboard differs from SQL

**Symptom:** national total matches but Dhaka does not. **Likely bugs:** relationship/filter direction, stale import, implicit average, or region label mismatch. **Diagnosis:** verify row counts and slicers, test numerator/denominator cards, inspect relationships, refresh source, and compare one region at a time.
