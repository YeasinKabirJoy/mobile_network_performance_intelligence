-- name: 07_regional_measurement_volume
SELECT
    r.adm1_name,
    COUNT(*) AS tiles,
    SUM(f.tests) AS tests,
    SUM(f.devices) AS devices,
    SUM(f.tests) * 1.0 / NULLIF(SUM(f.devices), 0) AS tests_per_device
FROM fact_tile_performance AS f
JOIN dim_region AS r USING (adm1_iso)
GROUP BY r.adm1_name
ORDER BY tests DESC;

-- name: 08_regional_weighted_performance
SELECT
    r.adm1_name,
    SUM(f.avg_d_mbps * f.tests) / NULLIF(SUM(f.tests), 0) AS weighted_download_mbps,
    SUM(f.avg_u_mbps * f.tests) / NULLIF(SUM(f.tests), 0) AS weighted_upload_mbps,
    SUM(f.avg_lat_ms * f.tests * 1.0) / NULLIF(SUM(f.tests), 0) AS weighted_idle_latency_ms,
    SUM(f.tests) AS denominator_tests
FROM fact_tile_performance AS f
JOIN dim_region AS r USING (adm1_iso)
GROUP BY r.adm1_name
ORDER BY weighted_download_mbps;

-- name: 09_regional_weighted_unweighted_gap
SELECT
    r.adm1_name,
    AVG(f.avg_d_mbps) AS unweighted_download_mbps,
    SUM(f.avg_d_mbps * f.tests) / NULLIF(SUM(f.tests), 0) AS weighted_download_mbps,
    SUM(f.avg_d_mbps * f.tests) / NULLIF(SUM(f.tests), 0) - AVG(f.avg_d_mbps)
        AS weighted_minus_unweighted_mbps
FROM fact_tile_performance AS f
JOIN dim_region AS r USING (adm1_iso)
GROUP BY r.adm1_name
ORDER BY ABS(weighted_minus_unweighted_mbps) DESC;

-- name: 10_regional_rankings
WITH regional AS (
    SELECT
        r.adm1_name,
        SUM(f.avg_d_mbps * f.tests) / NULLIF(SUM(f.tests), 0) AS weighted_download_mbps,
        SUM(f.avg_lat_ms * f.tests * 1.0) / NULLIF(SUM(f.tests), 0) AS weighted_idle_latency_ms,
        SUM(f.tests) AS tests
    FROM fact_tile_performance AS f
    JOIN dim_region AS r USING (adm1_iso)
    GROUP BY r.adm1_name
)
SELECT
    *,
    RANK() OVER (ORDER BY weighted_download_mbps DESC) AS download_rank_best_first,
    RANK() OVER (ORDER BY weighted_idle_latency_ms ASC) AS latency_rank_best_first
FROM regional
ORDER BY download_rank_best_first;

-- name: 11_regional_volume_mix
SELECT
    r.adm1_name,
    f.measurement_volume,
    COUNT(*) AS tiles,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY r.adm1_name), 2)
        AS region_tile_percent
FROM fact_tile_performance AS f
JOIN dim_region AS r USING (adm1_iso)
GROUP BY r.adm1_name, f.measurement_volume
ORDER BY r.adm1_name, CASE f.measurement_volume WHEN 'low' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END;

-- name: 12_regional_loaded_latency_missingness
SELECT
    r.adm1_name,
    COUNT(*) AS tiles,
    SUM(CASE WHEN f.avg_lat_down_ms IS NULL THEN 1 ELSE 0 END) AS missing_download_loaded_tiles,
    SUM(CASE WHEN f.avg_lat_up_ms IS NULL THEN 1 ELSE 0 END) AS missing_upload_loaded_tiles,
    ROUND(100.0 * SUM(CASE WHEN f.loaded_latency_complete = 0 THEN 1 ELSE 0 END) / COUNT(*), 2)
        AS incomplete_loaded_latency_percent
FROM fact_tile_performance AS f
JOIN dim_region AS r USING (adm1_iso)
GROUP BY r.adm1_name
ORDER BY incomplete_loaded_latency_percent DESC;

-- name: 13_download_speed_deciles
WITH ranked AS (
    SELECT
        avg_d_mbps,
        tests,
        NTILE(10) OVER (ORDER BY avg_d_mbps) AS download_decile
    FROM fact_tile_performance
)
SELECT
    download_decile,
    COUNT(*) AS tiles,
    MIN(avg_d_mbps) AS minimum_download_mbps,
    MAX(avg_d_mbps) AS maximum_download_mbps,
    SUM(tests) AS tests
FROM ranked
GROUP BY download_decile
ORDER BY download_decile;

-- name: 14_low_speed_high_latency_candidates
WITH thresholds AS (
    SELECT
        AVG(avg_d_mbps) AS mean_download_mbps,
        AVG(avg_lat_ms) AS mean_idle_latency_ms
    FROM fact_tile_performance
)
SELECT
    f.quadkey,
    r.adm1_name,
    f.avg_d_mbps,
    f.avg_lat_ms,
    f.tests,
    f.measurement_volume
FROM fact_tile_performance AS f
JOIN dim_region AS r USING (adm1_iso)
CROSS JOIN thresholds AS t
WHERE f.avg_d_mbps < t.mean_download_mbps
  AND f.avg_lat_ms > t.mean_idle_latency_ms
  AND f.tests >= 20
ORDER BY f.avg_d_mbps ASC, f.avg_lat_ms DESC
LIMIT 100;

-- name: 15_region_device_intensity
SELECT
    r.adm1_name,
    AVG(f.tests * 1.0 / f.devices) AS tile_avg_tests_per_device,
    SUM(f.tests) * 1.0 / NULLIF(SUM(f.devices), 0) AS aggregate_tests_per_device,
    MIN(f.tests * 1.0 / f.devices) AS minimum_tile_tests_per_device,
    MAX(f.tests * 1.0 / f.devices) AS maximum_tile_tests_per_device
FROM fact_tile_performance AS f
JOIN dim_region AS r USING (adm1_iso)
GROUP BY r.adm1_name
ORDER BY aggregate_tests_per_device DESC;
