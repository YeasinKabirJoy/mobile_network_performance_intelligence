# Phase 7 Power BI Management Dashboard

## What was built

- A reproducible exporter from the SQLite analytical database to four Power BI Import-mode tables.
- A star-style semantic model specification with shared region and quarter dimensions.
- Explicit DAX for counts, test-weighted performance, eligible latency denominators, data-quality warnings, priority, and dynamic scope.
- A management-page visual and interaction specification.
- A static, real-data build reference that is explicitly not presented as a Power BI screenshot.
- A reconciliation test for the default view plus Dhaka and Rajshani.
- Refresh, path-change, deployment, licensing, and troubleshooting guidance.

## Verified results

The export contains 15,956 tile rows, 8 region rows, 1 quarter row, and 8 region-priority rows. All six dashboard KPIs reconcile exactly or within floating-point tolerance (`1e-9`) for all three filter states. The only nonzero difference is approximately `1.78e-15` Mbps for Rajshani upload, which is ordinary floating-point representation and passes the tolerance.

## Acceptance status

The data, model, DAX, filters, interactions, warnings, and reconciliation targets are ready. Power BI Desktop is installed, but the available computer-control surface exposed no native application window. Therefore a `.pbix`, true in-app screenshots, and visual interaction demonstration remain the learner's Desktop checkpoint. No screenshot or dashboard file has been fabricated.

## Limitations carried into the dashboard

- Tiles are quarterly aggregates, not towers or raw individual tests.
- Tests and summed tile device counts are not subscribers or population.
- The single quarter supports filtering but not a trend claim.
- Map marks represent observed measurement tiles, not coverage.
- Investigation priority is a transparent hypothesis generator, not a fault diagnosis.
