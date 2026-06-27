# Standard — Testing Philosophy

Lazy-but-correct: **every non-trivial transform leaves ONE runnable check** — the smallest thing
that fails if the logic breaks. No frameworks/fixtures unless asked; an `assert`-based
`__main__` self-check or a tiny `test_*.py` is enough.

## What must have a check
- **Missing-value handling:** asserts the chosen rule produces no NaNs in scored output and respects the cluster logic (A2–A4).
- **Normalization/scaling:** asserts ranges are comparable before weighting (guards the `f11`≈0.03 vs `f4`≈126K trap).
- **Scoring function:** asserts a hand-built tiny dataframe ranks the way business logic says it should (a high-spend/low-risk row outranks a low-spend/high-cost row).
- **Submission builder:** asserts exactly 500K rows, all `id`s present once, no nulls in `Prediction`, column names match the template, `id` not used as a feature.

## What does NOT need a test
- Trivial one-liners, plotting code, throwaway EDA.

## Sanity over coverage
There's no ground-truth label to unit-test accuracy against. The real "test" of correctness is
**business plausibility + top-20% stability across resamples** (`validation.py`), not a number.
