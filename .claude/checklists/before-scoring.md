# Checklist — Before Scoring the Full 500K

_(The "before training" gate, adapted: this problem scores via a framework, not model training.)_

- [ ] Missing values handled by the **documented rule** per cluster (A2–A4); no NaNs will reach output.
- [ ] All components **normalized to comparable scales** before weighting (guards `f11` vs `f4` trap).
- [ ] `f7` negatives handled deliberately (A6); `f5` not treated as sum of `f6`–`f10` (A1).
- [ ] Every weight maps to a revenue/cost rationale in `business-context.md`.
- [ ] `id` excluded from the equation; only `f1`–`f23` used.
- [ ] Scoring is deterministic (seed set, stable sort by `id`).
- [ ] Output is a continuous score suitable for rank-ordering to a top-20% cut.
- [ ] Hand-built tiny-dataframe check passes (high-value row outranks low-value row).
