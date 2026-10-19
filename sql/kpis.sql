-- name: 01_dataset_overview
SELECT
    quarter_label,
    COUNT(*) AS tiles,
    SUM(tests) AS tests,
    SUM(devices) AS devices,
    COUNT(DISTINCT adm1_iso) AS regions
FROM fact_tile_performance
GROUP BY quarter_label;

-- name: 02_overall_speed_kpis
SELECT
    AVG(avg_d_mbps) AS tile_avg_download_mbps,
    SUM(avg_d_mbps * tests) / NULLIF(SUM(tests), 0) AS test_weighted_download_mbps,
    AVG(avg_u_mbps) AS tile_avg_upload_mbps,
    SUM(avg_u_mbps * tests) / NULLIF(SUM(tests), 0) AS test_weighted_upload_mbps
FROM fact_tile_performance;

-- name: 03_overall_latency_kpis
SELECT
    AVG(avg_lat_ms) AS tile_avg_idle_latency_ms,
    SUM(avg_lat_ms * tests * 1.0) / NULLIF(SUM(tests), 0) AS test_weighted_idle_latency_ms
FROM fact_tile_performance;

-- name: 04_loaded_latency_kpis
SELECT
    COUNT(avg_lat_down_ms) AS eligible_download_loaded_tiles,
    SUM(CASE WHEN avg_lat_down_ms IS NOT NULL THEN tests ELSE 0 END) AS eligible_download_loaded_tests,
    SUM(CASE WHEN avg_lat_down_ms IS NOT NULL THEN avg_lat_down_ms * tests * 1.0 END)
        / NULLIF(SUM(CASE WHEN avg_lat_down_ms IS NOT NULL THEN tests ELSE 0 END), 0)
        AS test_weighted_download_loaded_latency_ms,
    COUNT(avg_lat_up_ms) AS eligible_upload_loaded_tiles,
    SUM(CASE WHEN avg_lat_up_ms IS NOT NULL THEN tests ELSE 0 END) AS eligible_upload_loaded_tests,
    SUM(CASE WHEN avg_lat_up_ms IS NOT NULL THEN avg_lat_up_ms * tests * 1.0 END)
        / NULLIF(SUM(CASE WHEN avg_lat_up_ms IS NOT NULL THEN tests ELSE 0 END), 0)
        AS test_weighted_upload_loaded_latency_ms
FROM fact_tile_performance;

-- name: 05_quality_control_totals
SELECT
    SUM(CASE WHEN measurement_volume = 'low' THEN 1 ELSE 0 END) AS low_volume_tiles,
    SUM(CASE WHEN loaded_latency_complete = 0 THEN 1 ELSE 0 END) AS incomplete_loaded_latency_tiles,
    SUM(CASE WHEN quality_note = 'none' THEN 1 ELSE 0 END) AS no_flag_tiles,
    SUM(CASE WHEN avg_lat_ms = 0 THEN 1 ELSE 0 END) AS zero_idle_latency_tiles,
    SUM(CASE WHEN boundary_ambiguous = 1 THEN 1 ELSE 0 END) AS boundary_ambiguous_tiles
FROM fact_tile_performance;

-- name: 06_quarter_coverage
SELECT
    period_start,
    quarter_label,
    COUNT(*) AS tiles,
    COUNT(DISTINCT adm1_iso) AS regions,
    SUM(tests) AS tests,
    SUM(devices) AS devices
FROM fact_tile_performance
GROUP BY period_start, quarter_label
ORDER BY period_start;
