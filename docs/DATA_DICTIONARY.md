# Source Data Dictionary

Dataset: Speedtest by Ookla Global Mobile Network Performance Map Tiles, Q4 2024. The observed physical schema and null counts are recorded in `reports/DATA_QUALITY_BASELINE.md`.

| Field | Meaning | Unit/type | Analytical caution |
|---|---|---|---|
| `quadkey` | Zoom-16 tile identifier | Text | Expected grain key within a quarter; not a tower or test ID. |
| `tile` / `tiles` | Tile polygon encoded as WKT | Geometry text, EPSG:4326 | Confirm the actual column name and parse before spatial use. |
| `tile_x` | Tile centroid longitude | Decimal degrees | Coordinate semantics must be verified; bbox membership is not precise country membership. |
| `tile_y` | Tile centroid latitude | Decimal degrees | Same boundary caution as `tile_x`. |
| `avg_d_kbps` | Mean download throughput for contributing tests in the tile | kbps | Divide by 1,000 for Mbps. A tile mean is not an individual result. |
| `avg_u_kbps` | Mean upload throughput for contributing tests in the tile | kbps | Divide by 1,000 for Mbps. |
| `avg_lat_ms` | Mean idle latency for contributing tests | ms | Lower is generally preferable; do not imply root cause. |
| `avg_lat_down_ms` | Mean latency under download load | ms | Sparse population is expected; never replace missing values with zero. |
| `avg_lat_up_ms` | Mean latency under upload load | ms | Sparse population is expected; never replace missing values with zero. |
| `tests` | Count of contributing tests | Integer count | Not subscribers or population; one device may contribute multiple tests. |
| `devices` | Count of unique contributing devices | Integer count | Not subscribers, residents, or market share. |

## Derived fields created in Phase 3

- `avg_d_mbps = avg_d_kbps / 1000`
- `avg_u_mbps = avg_u_kbps / 1000`
- `quarter_label`: stable `YYYY-QN` reporting label.
- `measurement_volume`: `low` for 1-4 tests, `medium` for 5-19, and `high` for 20+; descriptive, not an exclusion rule.
- `loaded_latency_complete`: true only when both loaded-latency metrics are present.
- `quality_note`: compact disclosure of low volume and/or missing loaded latency.
- `adm1_name` / `adm1_iso`: region attributes assigned using the documented centroid rule.
- `boundary_ambiguous`: whether a centroid intersected multiple ADM1 features before deterministic tie resolution.
- `period_start`, `year`, `quarter`, `source_layer`: explicit temporal and provenance fields.

## Dataset grain

One aggregated zoom-16 geographic tile for one quarterly source file. Combining periods without a quarter key would violate the intended grain.
