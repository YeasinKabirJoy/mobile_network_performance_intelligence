# Project Presentation Scripts

## 60-second pitch

I built an end-to-end mobile network performance intelligence project using verified Q4 2024 Ookla mobile map tiles for Bangladesh. I filtered 3.55 million global tiles to 15,956 Bangladesh observations using a bounding box followed by ADM1 centroid assignment, then created a validated tile-quarter dataset and SQLite analytical model. Python and 15 SQL analyses reconcile on core KPIs: 37.63 Mbps test-weighted download, 16.04 Mbps upload, and 31.14 ms idle latency. EDA shows strong skew and that 80.2% of tiles have only one to four tests, so every comparison includes sampling caveats. I built a transparent regional priority score; Rajshani remains first under four weight scenarios, which suggests follow-up but does not prove a fault. Power BI and Tableau data/calculation handoffs reconcile to SQLite, with native workbook assembly still explicitly pending. The project emphasizes reproducibility, honest limits, and traceability from a real raw tile to regional decisions.

## Three-minute technical overview

The source is the official Ookla Q4 2024 mobile Parquet, verified at 195,139,957 bytes with 3,551,267 rows and a recorded checksum. I separately documented geoBoundaries ADM1 provenance. Rather than load the global file blindly, the extractor projects required columns and applies a Bangladesh bounding box, reducing the candidates to 49,213. It then creates EPSG:4326 centroids and applies a precise polygon predicate, retaining 15,956 rows across all eight divisions.

The cleaning layer enforces one quadkey per quarter, validates coordinates and counts, preserves weak and zero observations, keeps loaded-latency nulls, derives Mbps by dividing kbps by 1,000, and labels measurement volume. It produces both Parquet and CSV with hashes and an exclusion audit.

The persisted analytical engine is SQLite by learner choice. It contains a tile-performance fact and region dimension. Fifteen named queries demonstrate grouped KPIs, weighted and unweighted means, conditional denominators, CTEs, joins, window rankings, volume checks, and latency missingness. Eight Python/SQLite checks pass within `1e-9`.

EDA produces eight purposeful figures. The tile download median is 27.86 Mbps versus a 36.08 Mbps mean, showing right skew. Pearson and Spearman download-latency correlations are weak. Most importantly, 80.2% of tiles have one to four tests, so findings are descriptive, not population estimates.

The priority score converts regional speed weakness, latency weakness, and data sufficiency to rank percentiles, then applies transparent 45/35/20 weights. Persistence is zero-weight because only one quarter exists. Rajshani scores 86.79 and remains rank 1 under alternative weights, but the score is a hypothesis generator.

Finally, I created reconciled Power BI star-model imports/DAX and a Tableau flat map source/calculated fields. Both match SQLite for the national view, Dhaka, and Rajshani. A real Dhaka tile is traced from raw Parquet through extraction, cleaning, SQLite, EDA, scoring context, and both BI exports. Native PBIX/TWBX visual acceptance remains an honest manual checkpoint.

## Five-minute walkthrough

### 0:00-0:45 - business and boundaries

The business question is where public mobile-performance evidence suggests deeper regional investigation. The project serves analysts, operations managers, and planners. It does not support operator ranking, tower diagnosis, coverage claims, or outage detection because those fields and the required sampling design are absent.

### 0:45-1:30 - source and geography

The official source has 3.55 million quarterly tiles. Parquet lets the pipeline read selected columns efficiently. A numeric bounding box creates candidates, but it is not a country filter. A precise centroid-in-polygon rule assigns one Bangladesh ADM1 owner. The audit retains 15,956 rows, zero duplicate retained quadkeys, zero ambiguous centroids, and all eight regions.

### 1:30-2:15 - cleaning and SQLite

The declared grain is tile-quarter. The pipeline preserves raw kbps, derives Mbps, keeps null loaded latency as null, and labels evidence volume without deleting weak results. SQLite enforces the composite primary key and region foreign key. Weighted means are `SUM(metric*tests)/SUM(tests)`; loaded latency uses only eligible rows in both numerator and denominator.

### 2:15-3:00 - EDA

National test-weighted download is 37.625 Mbps. The typical tile median is lower at 27.865 Mbps because of right skew. Regional values vary: Sylhet has the highest weighted download at 45.496 Mbps, but participation and tile mix prevent causal interpretation. The download-latency association is weak. The critical caveat is that 12,797 tiles, or 80.2%, have only one to four tests.

### 3:00-3:45 - scoring

I normalized comparative speed, latency, and sufficiency to 0-1 percentiles and combined them with documented weights. Rajshani's components produce 86.786 and rank 1. It stays first when speed or latency emphasis changes, while middle ranks move. That stability justifies follow-up priority, not fault confirmation.

### 3:45-4:30 - trace and BI

Quadkey `1320222021021031` is an actual Dhaka tile: 28,630 kbps becomes 28.630 Mbps; it has 319 tests and contributes 9,132.97 Mbps-tests to Dhaka's numerator. Dhaka's full weighted download is 863,192.131 divided by 25,540, or 33.797656 Mbps. Python and SQLite match exactly; both BI input layers recalculate the same result. The row is ready for specified Power BI tooltips and Tableau selection actions.

### 4:30-5:00 - recommendation and honesty

I recommend investigating Rajshani with multiple quarters and direct site/operator/traffic evidence, elevating low-volume warnings in every decision view, and enforcing the automated quarterly refresh/reconciliation gate. The strongest portfolio feature is not a flashy rank; it is that every claim has lineage, denominator semantics, tests, and an explicit boundary on what the data cannot prove.

## Nontechnical management explanation

This project organizes public mobile-speed measurements into a regional screening tool. It shows where measured speed and latency look comparatively weaker and where there is enough evidence to justify a closer look. It does not tell us that a particular tower or operator failed. Rajshani is the most consistent follow-up candidate, but most map areas have few tests, so the appropriate next step is targeted validation with internal network and field information—not immediate remediation based only on this dashboard.

## Honest CV bullet

- Built a reproducible Python/GeoPandas/SQLite analytics pipeline for 3.55M public mobile-performance map tiles, producing a validated 15.9K-row Bangladesh dataset, 15 SQL analyses, EDA, transparent regional prioritization, real-record lineage, and cross-tool BI reconciliation with explicit sampling and causal limitations.

## Portfolio summary

Mobile Network Performance Intelligence is a phased analytics engineering project using official Ookla Q4 2024 mobile tiles and geoBoundaries ADM1 data. It demonstrates memory-aware Parquet inspection, precise geographic filtering, audited cleaning, SQLite modeling, intermediate SQL, statistical EDA, explainable composite scoring, BI semantic design, reconciliation, and end-to-end documentation. All reported values are generated from verified artifacts. Power BI and Tableau handoff calculations reconcile, while native workbook/screenshots remain clearly identified as pending manual acceptance rather than represented as completed.

## Evidence-to-claim checklist

- Source size/schema/checksum -> source manifest and inspection JSON.
- 15,956 retained rows -> extraction, cleaning, SQLite, EDA, and assurance audits.
- KPI values -> Python/SQLite/BI reconciliation JSON.
- EDA statements -> EDA summary and figures.
- Regional ranking -> scoring audit and sensitivity figure.
- Real tile -> final tile trace JSON.
- Recommendations -> business summary with necessary follow-up evidence.
