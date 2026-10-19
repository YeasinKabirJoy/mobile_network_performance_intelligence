# Cross-Tool Reconciliation

## Verified layers

| Comparison | Scope | Checks | Result |
|---|---|---:|---|
| Python vs SQLite | All Bangladesh, Q4 2024 | 8 | Pass |
| Power BI curated imports vs SQLite | All, Dhaka, Rajshani | 18 | Pass |
| Tableau flat export vs SQLite | All, Dhaka, Rajshani | 18 | Pass |

All automated differences are within absolute tolerance `1e-9`. The largest reported difference is ordinary floating-point representation at approximately `3.55e-15` for national weighted upload.

## Shared default-view KPIs

| KPI | Python | SQLite | Power BI import recalculation | Tableau export recalculation |
|---|---:|---:|---:|---:|
| Tiles | 15,956 | 15,956 | 15,956 | 15,956 |
| Tests | 62,785 | 62,785 | 62,785 | 62,785 |
| Devices* | 29,693 | 29,693 | 29,693 | 29,693 |
| Weighted download Mbps | 37.625394 | 37.625394 | 37.625394 | 37.625394 |
| Weighted upload Mbps | 16.039675 | 16.039675 | 16.039675 | 16.039675 |
| Weighted idle latency ms | 31.137915 | 31.137915 | 31.137915 | 31.137915 |

\* Summed tile-level unique-device counts, not globally deduplicated people or subscribers.

## Dashboard acceptance boundary

The Power BI and Tableau values above prove that the rows supplied to each tool and the documented formulas reconcile. They do not prove that an unbuilt or incorrectly configured native visual evaluates those formulas correctly. Native Desktop acceptance requires creating the measures/calculated fields, applying the specified filters, testing interactions, capturing genuine screenshots, and matching the same table for the default view, Dhaka, and Rajshani.
