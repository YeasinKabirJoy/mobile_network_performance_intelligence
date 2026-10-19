# KPI Definitions

All Phase 4 KPIs use Q4 2024 Bangladesh tiles unless an explicit region filter is applied. A filter changes both the numerator and denominator. SQLite stores the trusted tile-period fact rows; it does not reconstruct individual Speedtest observations.

## Core counts

| KPI | SQLite expression | Unit | Null/filter policy |
|---|---|---|---|
| Tiles | `COUNT(*)` | Tiles | Counts eligible fact rows after filters. |
| Tests | `SUM(tests)` | Tests | Source aggregate; not subscribers or sessions. |
| Devices | `SUM(devices)` | Device counts | Summing tile-level unique counts does not guarantee globally unique devices. |
| Regions | `COUNT(DISTINCT adm1_iso)` | ADM1 divisions | Uses assigned centroid region. |

## Throughput

| KPI | Formula | Interpretation |
|---|---|---|
| Unweighted tile download | `AVG(avg_d_mbps)` | Typical tile mean when every tile has equal influence. |
| Test-weighted download | `SUM(avg_d_mbps * tests) / SUM(tests)` | Reconstructed mean giving more influence to tiles with more tests. |
| Unweighted tile upload | `AVG(avg_u_mbps)` | Equal-weight mean of tile upload averages. |
| Test-weighted upload | `SUM(avg_u_mbps * tests) / SUM(tests)` | Reconstructed test-weighted upload mean. |

The weighted calculations use already-aggregated, potentially rounded tile means. They estimate a combined result and need not equal statistics calculated from unavailable raw tests.

## Latency

| KPI | Formula | Eligibility |
|---|---|---|
| Unweighted idle latency | `AVG(avg_lat_ms)` | Non-null idle-latency tiles. |
| Test-weighted idle latency | `SUM(avg_lat_ms * tests) / SUM(tests)` | Tests from rows with idle latency; all current rows qualify. |
| Test-weighted download-loaded latency | `SUM(avg_lat_down_ms * tests) / SUM(tests)` | Numerator and denominator include only rows where `avg_lat_down_ms IS NOT NULL`. |
| Test-weighted upload-loaded latency | `SUM(avg_lat_up_ms * tests) / SUM(tests)` | Numerator and denominator include only rows where `avg_lat_up_ms IS NOT NULL`. |

Missing loaded latency is excluded from both numerator and denominator. It is never converted to zero.

## Current verified all-Bangladesh values

| KPI | Value |
|---|---:|
| Tiles | 15,956 |
| Tests | 62,785 |
| Devices | 29,693 |
| Unweighted tile download | 36.078125 Mbps |
| Test-weighted download | 37.625394 Mbps |
| Test-weighted upload | 16.039675 Mbps |
| Test-weighted idle latency | 31.137915 ms |
| Complete loaded-latency tiles | 15,483 |

For weighted download, the verified intermediate numerator is 2,362,310.347 Mbps-tests and the denominator is 62,785 tests.

## SQLite implementation notes

- `NULLIF(denominator, 0)` prevents division by zero.
- Multiplication by `1.0` forces real-number division when both inputs are integers.
- Explicit measures are preferred to implicit dashboard aggregation.
- Every dashboard must reproduce these definitions and filter eligibility exactly.
