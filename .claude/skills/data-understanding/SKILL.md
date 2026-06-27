---
name: data-understanding
description: Use when loading or inspecting the dataset — schema, dtypes, row counts, ranges, and decoding masked features. Invoke before EDA and whenever a feature's meaning or scale is in question.
---

# Data Understanding

## Purpose
Know exactly what the 500K×24 dataset contains, decode `f1`–`f23`, and confirm structural facts before analysis.

## Inputs
`docs/...data.xlsx`, `docs/feature_description.xlsx`, `.claude/memory/terminology.md`, `feature-notes.md`.

## Outputs
Verified schema, per-column ranges/dtypes, decoded names, and any new structural fact (→ assumptions/feature-notes).

## Invocation Conditions
- First touch of the data in a session.
- Whenever a number/scale looks surprising (e.g. f5 vs f6–f10).

## Workflow
1. Load (pandas if working; else the stdlib `zipfile`+`xml` reader — see standards/python.md).
2. Assert shape (500,000 × 24) and columns (`id`,`f1`–`f23`).
3. For each feature: min/max/mean, % missing, distinct-value sample. Compare to `feature-notes.md`.
4. Decode via `terminology.md`; flag anomalies (negatives, non-zero floors, scale mismatches).
5. Persist any new fact to `assumptions.md`/`feature-notes.md`.

## Best Practices
- Read by column name, never position. Verify the env isn't lying (broken pandas stub).
- Don't trust slide-9 attribute names that aren't in the dictionary (tenure/bureau/wallet are absent).

## Common Mistakes
- Assuming `f5` = sum of category spends (A1).
- Assuming missing = 0 (missingness is structured — A2–A4).
- Using `id` as anything but a key.

## Example Usage
"Load the data and confirm it matches memory." → shape/columns assert pass → "Matches; f7 still shows negatives (refunds), f5 scale anomaly confirmed."
