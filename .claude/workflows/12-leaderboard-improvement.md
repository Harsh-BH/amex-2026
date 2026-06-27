# Workflow 12 — Leaderboard Improvement (Iteration)

**Objective:** Improve the score across the ≤10 submissions without overfitting the public 70%.
**Prerequisites:** A baseline submission + its public-LB result.

## Steps
1. Invoke **error-analysis** on the latest result: decompose top/cutoff members; find a systematic mismatch pattern.
2. Form ONE business-justified hypothesis (`/experiment`).
3. Validate internally (Workflow 11) before spending a submission.
4. Submit only if it survives internally and makes business sense; log result.
5. Consult **leaderboard-strategist** on budget/overfit before each submission.

## Validation
- Each iteration changes one thing; top-20% churn tracked; public gain is business-explained.

## Deliverables
- Updated framework + experiment records; improved (robust) score.

## Exit criteria
- Diminishing returns or budget low → lock in the most defensible submission.
