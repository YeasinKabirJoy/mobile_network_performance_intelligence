# Phase 5 Exploratory Data Analysis

Scope: 15,956 retained Q4 2024 Bangladesh mobile-performance tiles, representing 62,785 tests and 29,693 tile-level device counts. All findings are descriptive.

## Figure-by-figure analytical contract

| Figure | Business question | Aggregation and rationale | Actual observation | Limitation |
|---|---|---|---|---|
| `01_download_distribution.png` | How variable are tile download measurements? | Histogram of tile-average Mbps; mean and median expose skew. | Median 27.8645 Mbps; mean 36.0781; p95 94.1303; right skew 3.5795. | Tiles receive equal visual weight regardless of tests. |
| `02_upload_distribution.png` | How variable are tile upload measurements? | Histogram of tile-average Mbps. | Median 11.116 Mbps; mean 14.7796; p95 39.2605; right skew 1.3619. | Aggregated tiles are not individual-test distributions. |
| `03_idle_latency_distribution.png` | Is latency concentrated with a long tail? | Full histogram plus a p99 detail panel preserves extreme evidence while showing the center. | Median 27 ms; p95 56 ms; p99 154 ms; maximum 1,138 ms. | Extreme values are not confirmed faults and need corroboration. |
| `04_regional_download_boxplot.png` | How do tile distributions differ by division? | Per-tile boxplots show medians and dispersion without imposing test weights. | Regional medians range from 24.2615 Mbps in Rangpur to 34.546 Mbps in Sylhet. | Displayed whiskers hide fliers for scale; the source still retains them. |
| `05_regional_weighted_throughput.png` | How do reconstructed test-weighted speeds compare by division? | Bars use `SUM(tile mean × tests) / SUM(tests)`. | Weighted download ranges from 33.7977 Mbps in Dhaka to 45.4964 Mbps in Sylhet. | Uneven participation and rounded tile averages limit inference. |
| `06_download_latency_scatter.png` | Are faster tiles consistently associated with lower latency? | Tile scatter, colored by evidence volume; symlog latency reveals the long tail. | Pearson correlation is -0.0731 and Spearman is -0.1576: weak negative association. | Correlation is not causation and low-volume tiles dominate. |
| `07_measurement_volume.png` | How uneven is measurement participation? | Tests-per-tile histogram and categorical counts. | Median is two tests; 12,797 tiles (80.20%) are low-volume. | Test density is not population density or coverage. |
| `08_download_map.png` | Where do measured tile speeds vary geographically? | Actual tile centroids colored by download Mbps, with color capped at p95 for contrast. | The map shows substantial local variation and visible concentration around measured areas. | It cannot prove coverage gaps, tower locations, or operator performance. |

## Evidence-backed findings

### 1. Throughput distributions are strongly right-skewed

Download mean (36.0781 Mbps) exceeds the median (27.8645 Mbps), and the maximum reaches 532.573 Mbps. Upload shows the same direction, with a 14.7796 Mbps mean versus an 11.116 Mbps median. Means alone therefore overstate the center of the typical tile distribution.

**Operational interpretation:** use median and percentile context alongside averages when describing a typical area.

**Caveat:** these are distributions of quarterly tile averages, not raw user tests.

### 2. Evidence volume is highly uneven

The median tile contains two tests, while 12,797 of 15,956 tiles (80.20%) have only one to four tests. Only 427 tiles are classified as high-volume with at least 20 tests.

**Operational interpretation:** low-volume areas need additional measurement or corroborating operational data before prioritization.

**Caveat:** the chosen categories disclose evidence volume but are not confidence intervals or proof of representativeness.

### 3. Regional weighted download values differ descriptively

Test-weighted download ranges from 33.7977 Mbps in Dhaka to 45.4964 Mbps in Sylhet, an observed gap of approximately 11.70 Mbps. Sylhet also has the highest weighted upload value at 20.4539 Mbps.

**Operational interpretation:** regional drill-down may identify useful starting points for investigation and peer comparison.

**Caveat:** the result reflects uneven voluntary Speedtest participation and does not establish operator quality, resident experience, or causation.

### 4. Latency rankings tell a different story from download rankings

Rajshani has a test-weighted idle latency of 43.2522 ms, while Dhaka has 26.3806 ms. Rangpur combines comparatively high weighted download (42.5034 Mbps) with comparatively high weighted latency (39.9140 ms), showing that one metric cannot summarize performance.

**Operational interpretation:** prioritize multi-metric investigation instead of a download-only league table.

**Caveat:** latency outliers and differing test contexts can materially affect weighted values.

### 5. Download and idle latency have only weak negative association

The Pearson correlation is -0.0731 and the Spearman rank correlation is -0.1576. Faster download tiles are not consistently paired with proportionally lower idle latency in this aggregate sample.

**Operational interpretation:** evaluate speed and latency separately in dashboards and scoring.

**Caveat:** association at tile level cannot identify mechanisms, and the ecological fallacy applies.

### 6. Weighting materially changes some regional results

Rangpur's unweighted tile download mean is 33.9109 Mbps, while its test-weighted result is 42.5034 Mbps, a difference of 8.5925 Mbps. Tiles with more tests have higher influence under the weighted definition.

**Operational interpretation:** every published KPI must state whether it is tile-weighted or test-weighted.

**Caveat:** test weighting does not make the sample population-representative and uses rounded tile means rather than raw tests.

## Additional quality observations

- 2,264 tiles (14.19%) have download below 10 Mbps.
- 325 tiles (2.04%) have idle latency above 100 ms.
- 473 tiles (2.96%) lack at least one loaded-latency value.

These are descriptive screening counts, not outage, fault, or service-level classifications.

## Time limitation

Only Q4 2024 is in scope. No daily, monthly, quarter-over-quarter, persistence, or real-time trend claim is supported in Phase 5.
