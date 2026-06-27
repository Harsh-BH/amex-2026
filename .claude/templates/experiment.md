# Experiment exp-NNN — <slug>

- **Date:** YYYY-MM-DD
- **Hypothesis:** <one line: what change, expected effect, business reason>
- **Baseline:** exp-NNN (public LB = X)
- **Change:** <the single thing that differs — feature/transform/weight/missing-rule>
- **Config / seed:** <config version, SEED, scoring code commit/tag>

## Internal validation (before submitting)
- Top-20% stability across resamples: <result>
- Score distribution sanity: <result>
- Plausibility: do the new top members make business sense? <yes/no + why>

## Result
- **Public LB:** <score>  (Δ vs baseline: <+/->)
- **Private LB:** (hidden until R1 end)
- **Top-20% churn vs baseline:** <how many members entered/left the top quintile>

## Decision
- [ ] Keep / [ ] Kill / [ ] Iterate — because <reason>
- Submission budget after this: <n>/10

## Notes
<surprises, follow-ups, link to decision-log if this changed direction>
