# Phase 6 Explainable Priority Scoring

## Purpose and grain

This phase prioritizes follow-up investigation across Bangladesh's eight ADM1 regions for Q4 2024. One output row represents one region-quarter aggregation of public mobile-performance map tiles. The score is comparative within these eight regions; it is not a service-level threshold, fault probability, coverage measure, or operator assessment.

## Method

Regional speed and latency inputs are test-weighted reconstructions from the cleaned tile data. Each score component is converted to a deterministic 0-1 rank percentile so Mbps, milliseconds, and evidence volume can be combined without mixing raw units.

| Component | Construction | Direction | Base weight |
|---|---|---:|---:|
| Speed weakness | Mean of download- and upload-weakness percentiles | Lower speed raises priority | 45% |
| Latency weakness | Idle-latency percentile | Higher latency raises priority | 35% |
| Data sufficiency | Mean of log-test-volume and high-volume-tile-share percentiles | More evidence raises confidence | 20% |
| Persistence | Intended for repeated weak performance across quarters | More persistence would raise priority | 0% |

The base formula is:

`priority = 100 * (0.45 * speed weakness + 0.35 * latency weakness + 0.20 * data sufficiency)`

Persistence is null and receives zero weight because the current dataset contains only one quarter. No value is imputed. There are no invented good/bad network thresholds. Phase 3's low/medium/high test-volume bands are retained only as quality disclosures.

Average ranks handle tied component values. Final scenario ranks use shared minimum rank; ADM1 ISO provides deterministic display order only. Nullable loaded latency is excluded from the formula and its incompleteness is shown in each quality note. Scoring fails validation when a required speed, idle-latency, or volume input is absent rather than silently filling it.

## Base priority dataset

| Rank | ADM1 | Score | Primary explanation | Quality note |
|---:|---|---:|---|---|
| 1 | Rajshani | 86.79 | High idle latency and weak speed | 84.8% low-volume tiles; persistence unavailable |
| 2 | Barisal | 65.36 | Weak speed and high idle latency | 81.0% low-volume tiles; persistence unavailable |
| 3 | Rangpur | 62.50 | High idle latency with stronger evidence volume | 82.7% low-volume tiles; persistence unavailable |
| 4 | Dhaka | 55.36 | Stronger evidence volume and weak speed | 73.9% low-volume tiles; persistence unavailable |
| 5 | Chittagong | 47.14 | Stronger evidence volume and high idle latency | 80.9% low-volume tiles; persistence unavailable |
| 6 | Khulna | 38.57 | Weak speed and high idle latency | 86.0% low-volume tiles; persistence unavailable |
| 7 | Mymensingh | 30.00 | Weak speed with stronger evidence volume | 87.6% low-volume tiles; persistence unavailable |
| 8 | Sylhet | 14.29 | High idle latency with stronger evidence volume | 79.9% low-volume tiles; persistence unavailable |

The full CSV and Parquet outputs retain all inputs, components, scenario scores, ranks, explanations, and quality notes.

## Three auditable traces

1. **Rajshani:** download 34.1667 Mbps, upload 13.8748 Mbps, idle latency 43.2522 ms, 4,706 tests. Components are speed 0.928571, latency 1.000000, sufficiency 0.500000. `100 * (0.45*0.928571 + 0.35*1 + 0.20*0.5) = 86.7857`, rank 1.
2. **Barisal:** download 35.0500 Mbps, upload 14.6525 Mbps, idle latency 32.1518 ms, 3,385 tests. Components are speed 0.785714, latency 0.571429, sufficiency 0.500000. The score is 65.3571, rank 2.
3. **Rangpur:** download 42.5034 Mbps, upload 15.0572 Mbps, idle latency 39.9140 ms, 4,976 tests. Components are speed 0.500000, latency 0.857143, sufficiency 0.500000. The score is 62.5000, rank 3.

These traces explain the arithmetic, not the cause of the observations.

## Sensitivity analysis

Four scenarios were tested: base, speed emphasis, latency emphasis, and lower volume influence. Rajshani remains rank 1, Barisal remains in the top three, Mymensingh remains rank 7, and Sylhet remains rank 8 in every scenario. Middle positions are less stable: emphasizing speed moves Dhaka from 4 to 3; emphasizing latency moves Rangpur from 3 to 2, Chittagong from 5 to 4, and Dhaka from 4 to 6. Lowering the sufficiency weight does not change the base order.

The stable top result supports Rajshani as a robust first follow-up under these stated preferences. Movement in the middle warns users not to treat small rank differences as objective truth.

## Interpretation and limitations

The score answers: "Given these comparative measurements and documented preferences, where should an analyst investigate first?" It does not answer why performance differs. The public aggregates do not identify towers, operators, subscribers, population, outages, radio conditions, backhaul, device capability, or root cause. Most tiles have low test volume, and measurement participation is not random. A real investigation should combine additional quarters, operator/network telemetry, site inventory, incident history, demand or population context, and field validation.
