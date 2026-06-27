---
name: exploratory-data-analysis
description: Use to explore feature distributions, correlations, segments, and missingness patterns on the 500K dataset. Invoke via /eda or before designing the framework, to ground every modeling choice in evidence.
---

# Exploratory Data Analysis

## Purpose
Turn raw columns into evidence: distributions, relationships, segments, and missingness structure that inform feature selection, transforms, and weights.

## Inputs
Loaded dataset; `feature-notes.md`; `business-context.md`.

## Outputs
Figures + a written report (`templates/report.md`) and updates to `feature-notes.md`. No leakage of `id`.

## Invocation Conditions
- After data-understanding, before framework-design.
- When a transform/weight decision needs evidence.

## Workflow
1. **Univariate:** distribution + skew + outliers per feature; log-scale the heavy-tailed spends (`f4`,`f7`,`f21`).
2. **Missingness map:** confirm the co-missing clusters (A2–A4); test if missing rows differ systematically.
3. **Relationships:** correlations among spends; spend vs rewards (`f21`) vs risk (`f11`); benefit usage vs spend.
4. **Segments:** charge-only (no `f17`/`f18`) vs lenders; rewards vs non-rewards population.
5. **Proxy-profit sanity:** eyeball who looks profitable vs costly; does it match business intuition?
6. Record takeaways; promote durable facts to memory.

## Best Practices
- Every figure gets a one-line takeaway caption. Vectorize over 500K rows.
- Look at the *top tail* specifically — the metric only cares about the top 20%.

## Common Mistakes
- Correlation hunting without a business hypothesis.
- Ignoring missingness as a segment signal.
- Optimizing global structure when only the top quintile is scored.

## Example Usage
"/eda on spend features." → log-dist plots + correlation of f5–f10 + note that f6/f9 (5x cats) drive rewards cost.
