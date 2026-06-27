---
name: experiment-tracking
description: Use whenever running a scoring variant or preparing a submission — record hypothesis, config, and result so the ≤10 submissions are spent wisely and results are reproducible. Invoke via /experiment.
---

# Experiment Tracking

## Purpose
Make every scoring attempt a logged, reproducible, hypothesis-driven experiment — protecting the 10-submission budget.

## Inputs
The change being tested; seed/config; baseline.

## Outputs
An `exp-NNN` record (`templates/experiment.md`) + a row in `memory/experiment-history.md`.

## Invocation Conditions
- Before any scoring variant or submission.

## Workflow
1. Write the **hypothesis first** (what/expected/why).
2. Capture config + seed + scoring commit/tag.
3. Run internal validation (evaluation skill) before deciding to submit.
4. If submitting, decrement the budget counter; record public-LB result after.
5. Keep/kill/iterate decision; link any direction change to `decision-log.md`.

## Best Practices
- One variable changed per experiment.
- Internal validation before a real submission whenever possible.
- Track top-20% membership churn, not just the score.

## Common Mistakes
- Submitting without a hypothesis (wasted budget).
- Not recording config → irreproducible result.
- Letting the history table drift out of sync with reality.

## Example Usage
"/experiment cap f4 at p99." → log exp-005 hypothesis → validate internally → submit if promising → record LB + decision.
