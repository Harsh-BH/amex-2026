# Workflow 06 — Data Cleaning & Missing-Value Strategy

**Objective:** A documented, tested treatment of missing/anomalous values so scoring is correct.
**Prerequisites:** Workflow 05.

## Steps
1. Invoke **missing-value-analysis**.
2. Decide a rule per cluster (`f6`–`f10`; `f4`+`f21`; `f13`–`f16`; `f17`/`f18`; `f23`): structural-as-0+flag vs reasoned impute.
3. Decide `f7` negatives treatment (A6) and confirm `f5` is not summed (A1).
4. Implement in `src/features.py`; assert no NaN reaches the score.

## Validation
- Tiny-dataframe check + full-data assert: zero NaN in scored output; flags computed correctly.

## Deliverables
- Cleaning/missing rules in code + documented in `framework-doc.md` transformations.

## Exit criteria
- Data is score-ready with no silent fills; rules are reproducible.
