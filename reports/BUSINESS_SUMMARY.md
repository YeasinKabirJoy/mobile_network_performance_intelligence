# Mobile Network Performance Intelligence - Business Summary

## Problem and decision context

Regional operations and planning teams need a defensible way to screen public mobile-performance measurements, compare administrative regions, and decide where deeper investigation may be worthwhile. This project converts verified Q4 2024 Ookla map-tile aggregates for Bangladesh into a reproducible SQLite analytical pipeline, descriptive analysis, transparent priority score, and BI-ready management/exploration packages.

The output supports prioritization and hypothesis formation. It does not identify operators, towers, subscribers, population coverage, outages, technology generations, or root causes.

## Data and method

- Official Q4 2024 mobile Parquet file, accessed 19 October 2026 and preserved with source URL, byte size, and SHA-256.
- Bangladesh ADM1 boundaries from geoBoundaries, with separate provenance and license.
- Bounding-box candidate filter followed by centroid-to-ADM1 polygon assignment.
- Reusable cleaning with declared tile-quarter grain, preserved weak values, explicit loaded-latency nulls, and Mbps conversion.
- SQLite fact/dimension model and 15 named SQL analyses.
- Descriptive EDA, test-weighted regional reconstruction, transparent percentile score, and alternative-weight scenarios.
- Curated Power BI and Tableau imports with matching measure definitions and reconciliation evidence.

## Verified findings

1. **Observed scope:** 15,956 retained Bangladesh tile-quarter rows contain 62,785 tests and summed tile device counts of 29,693. The device total is not globally deduplicated and neither count represents subscribers or population.
2. **National descriptive performance:** test-weighted download is 37.625394 Mbps, upload is 16.039675 Mbps, and idle latency is 31.137915 ms. These reconstruct combined results from published tile averages rather than unavailable raw tests.
3. **Skew matters:** the mean tile download is 36.078125 Mbps while the median is 27.8645 Mbps; the positive gap and skew value of 3.5795 show that high tile values pull the mean upward.
4. **Evidence volume is uneven:** 12,797 tiles (80.20%) contain only 1-4 tests. Regional comparisons therefore combine network observations with uneven measurement participation.
5. **Regional variation is descriptive:** Sylhet has the highest test-weighted download at 45.496427 Mbps, while Dhaka has 33.797656 Mbps. This difference does not establish coverage, operator quality, congestion, or cause.
6. **Latency and priority warrant follow-up:** Rajshani has the highest test-weighted idle latency at 43.252231 ms and remains priority rank 1 under all four tested weight scenarios. That stability supports investigation priority, not a confirmed fault.
7. **Association is weak:** tile download and idle latency have Pearson correlation -0.0731 and Spearman correlation -0.1576. Neither statistic supports a causal explanation.

## Recommendations

1. **Investigate Rajshani with direct operational evidence.** Add multiple quarters, operator/network telemetry, site inventory, traffic demand, incident history, and field testing before attributing a fault or approving remediation.
2. **Treat low-volume evidence as an uncertainty control.** Display the 1-4-test warning in every decision view, compare results with and without low-volume tiles, and avoid investment decisions based on a small number of public measurements.
3. **Institutionalize the reproducible quarterly refresh.** Verify source checksums/schema, rerun extraction and validation, rebuild SQLite, regenerate both BI exports, and require cross-tool reconciliation before publishing findings.

## Limitations

- One quarter cannot support trend, persistence, seasonality, or live-monitoring claims.
- Public measurements are voluntary/observational and do not form a random population sample.
- Tiles are aggregated spatial units, not towers, sectors, sites, or individual tests.
- Tests and devices do not measure residents, subscribers, demand, or market share.
- Operator, radio technology, coverage, outage, call-quality, traffic, and causal fields are absent.
- Centroid assignment simplifies tiles crossing administrative boundaries.
- Loaded latency has expected missingness; nulls are excluded rather than replaced with zero.
- Power BI and Tableau calculations are reconciled at the import/export layer; native dashboard assembly and visual-interaction acceptance remain manual checkpoints.
