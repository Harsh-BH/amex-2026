# Checklist — Before Submission (CRITICAL)

A bad file wastes one of only 10 submissions. Verify all:

- [ ] File matches the **exact Unstop template** (`docs/...submission_template.xlsx`): both sheets, exact headers.
- [ ] `Predictions` sheet has **exactly 500,000 rows**, every `id` 0–499,999 present **once**, none missing/duplicated.
- [ ] **No null/blank** in the `Prediction` column.
- [ ] `Prediction` is a numeric score that rank-orders correctly (higher = more profitable).
- [ ] `id` was **not** used as a feature anywhere in deriving the score.
- [ ] Shared data was not altered, no rows added/removed.
- [ ] `Profitability Framework` sheet filled (Variables, Equation, Logic, Weights, Transforms, Business Logic, Assumptions, Validation, Notes) — from `templates/framework-doc.md`.
- [ ] Experiment logged with hypothesis BEFORE submitting; submission budget decremented.
- [ ] Filename `submission_v<N>_<desc>.xlsx`; scoring code committed/tagged for reproducibility.
- [ ] Sanity: score distribution and top-20% cutoff look reasonable (no degenerate all-equal scores).
