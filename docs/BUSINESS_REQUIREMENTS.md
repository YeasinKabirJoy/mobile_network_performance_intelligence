# Business Requirements

## Purpose

Create a defensible, reproducible view of geographic mobile-network performance patterns in Bangladesh using public quarterly Ookla map-tile aggregates. The output should help analysts identify areas that merit further investigation, not diagnose faults or rank operators.

## Stakeholders and decisions

| Stakeholder | Supported decision |
|---|---|
| Data analyst | Define and reproduce geographic KPIs and investigate unusual patterns. |
| Regional operations manager | Decide which divisions or tiles warrant validation with operational evidence. |
| Network planning team | Identify geographic areas for deeper capacity, coverage, or field-study review. |
| Management | Understand broad geographic differences, data sufficiency, and investigation priorities. |

## Answerable business questions

1. Which Bangladesh divisions show comparatively lower download or upload speeds in the selected quarter?
2. Which divisions or tiles show comparatively higher idle or loaded latency?
3. How do test-weighted regional means differ from unweighted tile means?
4. Where are test and device volumes too low for confident comparison?
5. Which areas combine weak measured performance with sufficient measurement volume to justify follow-up?
6. How strongly are download speed, upload speed, latency, and measurement volume associated?
7. If additional quarters are introduced later, which areas remain comparatively weak over time?

## Agreed Phase 1 scope

- Geography: Bangladesh, with future reporting at ADM1 division and tile levels.
- Time: Q4 2024 (2024-10-01 through 2024-12-31) for the initial implementation.
- Service: Ookla `performance_mobile_tiles` only.
- Phase 1 outcome: source and scope verification, not geographic extraction or performance findings.

Question 7 is conditional: persistence cannot be evaluated from a single quarter. Adding periods requires a later documented scope decision.

## Explicit non-goals

- Operator, technology-generation, tower, subscriber, population, outage, or root-cause analysis.
- Live monitoring, daily trends, individual test histories, or causal conclusions.
- Treating the number of tests or devices as population or market share.
- Publishing measurements before license, provenance, aggregation, and disclosure checks pass.

## Success criteria for the completed project

- Every reported number is reproducible from retained source artifacts.
- Equivalent filters and formulas reconcile across Python, SQL, Power BI, and Tableau.
- Findings distinguish observation from hypothesis and disclose sampling limitations.
- A user can trace one real tile and one KPI through the complete pipeline.
