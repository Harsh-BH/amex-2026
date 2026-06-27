# Workflow 05 — Exploratory Data Analysis

**Objective:** Evidence (distributions, relationships, segments, missingness) to ground design choices.
**Prerequisites:** Workflows 02–04.

## Steps
1. Invoke **exploratory-data-analysis** (`/eda`).
2. Univariate distributions (log-scale heavy tails); missingness map; correlations; segment behavior.
3. Specifically profile the **top tail** — only top-20% is scored.
4. Use **visualization** for captioned figures; write a `report.md`.
5. Promote durable findings to `feature-notes.md`.

## Validation
- Each figure has a takeaway; findings tie back to a business hypothesis.

## Deliverables
- EDA report + figures in `reports/`; updated memory.

## Exit criteria
- Enough evidence to choose transforms, features, and missing-value rules.
