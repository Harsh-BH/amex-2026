---
name: evaluation
description: Use to validate the score before submitting — replicate the top-20%-overlap metric on internal resamples, check stability, and guard against public-LB overfitting. Invoke via /evaluate before any submission.
---

# Evaluation

## Purpose
Estimate how well our top-20% will match the (hidden) actual top-20%, using internal resampling, since we have no ground-truth label.

## Inputs
The scored 500K; the scoring code; a fixed seed.

## Outputs
Top-20% stability metrics, score-distribution sanity, an overfit-risk read → keep/kill decision.

## Invocation Conditions
- Before every submission; after any scoring change.

## Workflow
1. **Cutoff:** compute the top-20% threshold on the full score; identify the top-quintile members.
2. **Stability:** repeatedly split 70/30 (mirroring the public/private design), re-rank within each, measure how consistently the same members land in the top 20%. Low churn = robust.
3. **Sensitivity:** re-run with perturbed weights/transforms; quantify top-20% membership drift.
4. **Distribution sanity:** no degenerate all-equal/ties-dominated scores; smooth, separating tail.
5. **Plausibility:** spot-check top members against business intuition (business-analysis skill).
6. Decide keep/kill; record in the experiment.

## Best Practices
- Optimize **top-tier separation**, not global correlation.
- A change that helps public LB but hurts internal stability is dangerous (private-LB risk).

## Common Mistakes
- Treating the public LB as ground truth.
- Reporting a single accuracy number with no stability/sensitivity context.
- Forgetting there's no real label — "accuracy" here is internal proxy + leaderboard.

## Example Usage
"/evaluate the v3 score." → top-20% Jaccard across 20 resamples = 0.94 (stable); distribution clean → safe to consider submitting.
