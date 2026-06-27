---
name: error-analysis
description: Use to diagnose WHY a scoring framework ranks members the way it does and where it likely mismatches the true profitability — inspect the top/bottom tail and disagreements. Invoke when a submission underperforms or before iterating.
---

# Error Analysis

## Purpose
Find systematic weaknesses in the ranking — which members are mis-ranked and why — to drive the next, hypothesis-led iteration (not random tweaking).

## Inputs
Scored 500K; the per-term contributions; public-LB delta; `business-context.md`.

## Outputs
A diagnosis (e.g. "cost terms under-weighted for high-benefit/low-spend members") → a concrete next experiment.

## Invocation Conditions
- After a submission result; before spending another submission.

## Workflow
1. **Decompose:** for top-quintile and just-below-cutoff members, break the score into term contributions — what's driving inclusion?
2. **Find suspects:** members the framework ranks high that look unprofitable by business sense (high benefit burn, high risk, low spend) — and the reverse.
3. **Pattern, not anecdote:** is the mismatch concentrated in a segment (charge-only? rewards-heavy?)?
4. **Hypothesize a fix:** one change addressing the pattern; predict its effect.
5. Feed into an experiment record.

## Best Practices
- Focus on the **cutoff boundary** — that's where overlap is won/lost.
- One hypothesis per iteration; measure top-20% churn.

## Common Mistakes
- Tweaking many things at once → can't attribute the change.
- Reacting to public-LB noise without a business pattern.

## Example Usage
"Why did v2 drop?" → high-`f4`-rewards-balance members dominate the top via an un-normalized term → hypothesis: normalize/cap `f4`, re-evaluate.
