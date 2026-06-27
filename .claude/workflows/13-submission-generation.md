# Workflow 13 — Submission Generation

**Objective:** A template-valid submission file that won't waste one of the 10 attempts.
**Prerequisites:** A scored, evaluated framework + a logged hypothesis.

## Steps
1. Run **`/submit`**; build BOTH sheets from the exact template.
2. `Predictions`: all 500K `id`s once, no null `Prediction`, numeric rank-ordering.
3. `Profitability Framework`: copy from `framework-doc.md`, consistent with `scoring.py`.
4. Run the **`before-submission` checklist** end to end.
5. Dispatch the **submission-validator** agent as a final mechanical gate.
6. Commit/tag the scoring code; decrement the budget.

## Validation
- submission-validator returns PASS; checklist fully green.

## Deliverables
- `submissions/submission_v<N>_<desc>.xlsx`; experiment row updated.

## Exit criteria
- File uploaded; public-LB result recorded in `experiment-history.md`.
