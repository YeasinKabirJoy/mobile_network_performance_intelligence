PRAGMA foreign_keys = ON;

CREATE TABLE project_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
);

CREATE TABLE dim_region (
    adm1_iso TEXT PRIMARY KEY,
    adm1_name TEXT NOT NULL UNIQUE
);

CREATE TABLE fact_tile_performance (
    quadkey TEXT NOT NULL,
    period_start TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 2019),
    quarter INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    quarter_label TEXT NOT NULL,
    source_layer TEXT NOT NULL,
    adm1_iso TEXT NOT NULL REFERENCES dim_region(adm1_iso),
    tile_wkt TEXT NOT NULL,
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    avg_d_kbps INTEGER NOT NULL CHECK (avg_d_kbps >= 0),
    avg_u_kbps INTEGER NOT NULL CHECK (avg_u_kbps >= 0),
    avg_d_mbps REAL NOT NULL CHECK (avg_d_mbps >= 0),
    avg_u_mbps REAL NOT NULL CHECK (avg_u_mbps >= 0),
    avg_lat_ms INTEGER NOT NULL CHECK (avg_lat_ms >= 0),
    avg_lat_down_ms INTEGER CHECK (avg_lat_down_ms >= 0),
    avg_lat_up_ms INTEGER CHECK (avg_lat_up_ms >= 0),
    tests INTEGER NOT NULL CHECK (tests > 0),
    devices INTEGER NOT NULL CHECK (devices > 0 AND devices <= tests),
    measurement_volume TEXT NOT NULL CHECK (measurement_volume IN ('low', 'medium', 'high')),
    loaded_latency_complete INTEGER NOT NULL CHECK (loaded_latency_complete IN (0, 1)),
    quality_note TEXT NOT NULL,
    boundary_ambiguous INTEGER NOT NULL CHECK (boundary_ambiguous IN (0, 1)),
    PRIMARY KEY (quadkey, period_start)
);

CREATE INDEX idx_fact_region_period
    ON fact_tile_performance (adm1_iso, period_start);

CREATE INDEX idx_fact_period_volume
    ON fact_tile_performance (period_start, measurement_volume);

CREATE VIEW v_tile_performance AS
SELECT
    f.*,
    r.adm1_name
FROM fact_tile_performance AS f
JOIN dim_region AS r USING (adm1_iso);
