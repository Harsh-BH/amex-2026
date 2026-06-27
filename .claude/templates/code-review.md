# Code Review — <target>

_Two lenses: correctness bugs AND over-engineering (Ponytail). Be specific: file:line, what, fix._

## Correctness
- [ ] No `id` used as a feature; no data leakage from the split.
- [ ] Missing values handled per documented rule; no accidental NaN/0 fill.
- [ ] Scales normalized before weighting; `f5`/`f7` traps avoided.
- [ ] Deterministic (seed, stable sort); output is exactly 500K valid rows.
- [ ] Errors fail loud at load/write boundaries.

## Simplification / efficiency
- [ ] Anything reinventing stdlib/pandas? Replace.
- [ ] Speculative abstraction / unused flexibility? Delete.
- [ ] Loops over 500K rows that should be vectorized?

## Findings
| file:line | issue | severity | suggested fix |
|---|---|---|---|

## Verdict
<approve / changes requested + summary.>
