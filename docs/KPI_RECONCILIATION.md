# Four-Environment KPI Reconciliation

## KPI and common filter

KPI: test-weighted download Mbps by region and quarter.

Filter: Dhaka (`BD-C`), Q4 2024. Eligible population: every retained clean tile in Dhaka for that quarter; download is non-null for all current rows.

## Python proof

```python
selected = frame[(frame["adm1_iso"] == "BD-C") &
                 (frame["quarter_label"] == "2024-Q4")]
numerator = (selected["avg_d_mbps"] * selected["tests"]).sum()
denominator = selected["tests"].sum()
result = numerator / denominator
```

- Numerator: 863,192.131 Mbps-tests.
- Denominator: 25,540 tests.
- Result: 33.797655873 Mbps.
- Status: verified by `src.final_trace`.

## SQLite proof

```sql
SELECT
    SUM(avg_d_mbps * tests) AS numerator,
    SUM(tests) AS denominator,
    SUM(avg_d_mbps * tests) / (SUM(tests) * 1.0) AS weighted_download_mbps
FROM fact_tile_performance
WHERE adm1_iso = 'BD-C'
  AND quarter_label = '2024-Q4';
```

The result is 863,192.131 / 25,540 = 33.797655873 Mbps. Python-SQLite absolute difference is 0.0; tolerance is `1e-9`; automated status is pass.

## Power BI definition

```DAX
Test-Weighted Download Mbps =
DIVIDE (
    SUMX (
        FactTilePerformance,
        FactTilePerformance[avg_d_mbps] * FactTilePerformance[tests]
    ),
    [Tests]
)
```

Required slicers: `DimRegion[adm1_name] = Dhaka` and `DimQuarter[quarter_label] = 2024-Q4`. The curated import rows independently recalculate to 33.797655873 Mbps and pass against SQLite. Native card evaluation is **not tested** because a PBIX could not be authored through the unavailable Windows control surface.

## Tableau definition

```text
SUM([avg_d_mbps] * [tests]) / SUM([tests])
```

Required filters: `adm1_name = Dhaka` and `quarter_label = 2024-Q4`. The flat export rows independently recalculate to 33.797655873 Mbps and pass against SQLite. Native worksheet evaluation is **not tested** because a TWB/TWBX could not be authored through the unavailable Windows control surface.

## Reconciliation table

| Environment | Numerator | Denominator | Result Mbps | Difference from SQLite | Status |
|---|---:|---:|---:|---:|---|
| Python | 863,192.131 | 25,540 | 33.797655873 | 0.0 | Pass |
| SQLite | 863,192.131 | 25,540 | 33.797655873 | 0.0 | Reference/pass |
| Power BI curated import | 863,192.131 | 25,540 | 33.797655873 | 0.0 | Import layer pass; native visual pending |
| Tableau flat export | 863,192.131 | 25,540 | 33.797655873 | 0.0 | Export layer pass; native visual pending |

## Interpretation

The same rows, units, filter, weight, numerator, and denominator reconcile. The overall four-environment acceptance remains partial until the explicit DAX and Tableau fields are evaluated in genuine Desktop visuals under the stated filters. Display rounding to 33.80 Mbps is acceptable; a material difference indicates a path, relationship, filter, type, aggregation, or eligibility defect.
