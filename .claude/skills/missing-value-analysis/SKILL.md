---
name: missing-value-analysis
description: Use when deciding how to handle missing values — which are structural (meaningful) vs random, and the imputation/flagging rule per feature cluster. Invoke before scoring; missingness here is a signal, not noise.
---

# Missing Value Analysis

## Purpose
Choose a defensible, documented treatment for each missing-data cluster so the score is correct and no NaN reaches output.

## Inputs
Loaded data; `feature-notes.md` (missing clusters); `assumptions.md` (A2–A4).

## Outputs
A per-cluster rule (impute value / add missing-flag / treat-as-absent), documented in the framework writeup + tested.

## Invocation Conditions
- Before any full-500K scoring run.
- Whenever a feature's missingness pattern changes the interpretation.

## Workflow
1. Quantify missing % per feature; confirm the co-missing clusters (`f6`–`f10`; `f4`+`f21`; `f13`–`f16`; `f17`/`f18`; `f23`).
2. Classify each cluster: **structural** (e.g. no lend line = charge-only → missing means "absent", treat as 0 + flag) vs **random** (impute with reasoned central value).
3. Decide: for cost/usage features, missing benefit usage likely = 0 cost; for spend, missing category may mean no breakdown, not zero spend — handle carefully.
4. Add a binary missing-flag where the *fact of* missingness is informative (e.g. `has_lend_line`).
5. Assert no NaN survives into the `Prediction`.

## Best Practices
- Different rule per cluster; never one global fillna.
- Keep the flag features but never let any of them be `id`-derived.

## Common Mistakes
- `fillna(0)` everywhere → distorts spend and risk.
- Imputing the mean into a heavily-skewed feature.
- Forgetting `f23` is 88% missing → weak signal, weight accordingly or drop.

## Example Usage
"Handle f17/f18 missingness." → "~60% missing = charge-only members; treat lend line as 0 and add `has_lend_line` flag; document as structural."
