# Geographic Extraction Report - Phase 2

Run date: 2026-10-19

## Purpose

Create a manageable, auditable Q4 2024 Bangladesh subset without loading the global source into memory and without modifying raw data.

## Inputs

- Verified Q4 2024 Ookla mobile Parquet: 3,551,267 global tile rows.
- geoBoundaries Bangladesh ADM1 GeoJSON: eight valid features in EPSG:4326.

## Method

1. Stream projected source columns from Parquet in batches.
2. Apply numeric longitude/latitude limits of 88.0-92.8 E and 20.5-26.7 N.
3. Convert the 49,213 candidate centroids to EPSG:4326 point geometry.
4. Join points to ADM1 polygons using `intersects`.
5. If a centroid exactly intersects multiple divisions, flag it and assign the alphabetically first `shapeISO`. No such tie occurred in this run.
6. Persist a GeoParquet subset, audit JSON, and validation map.

## Results

| Check | Result |
|---|---:|
| Global source rows | 3,551,267 |
| Bounding-box candidates | 49,213 |
| Retained Bangladesh centroids | 15,956 |
| Unmatched bbox candidates | 33,257 |
| Expected/observed ADM1 features | 8 / 8 |
| Duplicate retained quadkeys | 0 |
| Missing retained geometry | 0 |
| Invalid/empty boundary geometries | 0 / 0 |
| Ambiguous boundary centroids | 0 |

## Distribution by supplied ADM1 name

| ADM1 | Tiles | Tests | Devices |
|---|---:|---:|---:|
| Barisal | 961 | 3,385 | 1,368 |
| Chittagong | 4,022 | 13,813 | 6,971 |
| Dhaka | 4,420 | 25,540 | 11,811 |
| Khulna | 1,467 | 4,203 | 2,115 |
| Mymensingh | 709 | 1,900 | 995 |
| Rajshani | 1,582 | 4,706 | 2,356 |
| Rangpur | 1,524 | 4,976 | 2,195 |
| Sylhet | 1,271 | 4,262 | 1,882 |

`Rajshani` is preserved exactly from the chosen boundary release. Normalizing it to another spelling would be an explicit downstream data-cleaning decision.

## Outputs

- Interim GeoParquet: `data/interim/bgd_mobile_tiles_2024_q4.parquet`
- Size: 1,153,962 bytes
- SHA-256: `85CF316ABF9C18AF6F13DBF09A34DC15D551C561C09FFEDB3A713C2BB16F4553`
- Audit: `reports/generated/geographic_extraction_audit.json`
- Validation figure: `reports/figures/bgd_tile_centroids_2024_q4.png`
- Figure SHA-256: `D34B6BDD182018C637BBBE386812D4AF7A226CB91C60E372DE3EB330115D1661`

## Limitations

- Centroid assignment does not measure how much of each tile polygon overlaps a division.
- Unmatched bbox candidates are not errors; the rectangle includes neighboring territory and water.
- The point density visualizes source measurements, not cellular coverage, subscribers, or population.
- Administrative naming and represented-year limitations inherit from the selected geoBoundaries release.
