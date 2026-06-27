# Experiment History

_Every scoring attempt. **Submissions are capped at 10** — guard them. Log BEFORE submitting
(hypothesis) and AFTER (result). Use `.claude/templates/experiment.md` for full records; this
table is the index. Newest at top._

## Submission budget: 0 / 10 used

| # | Date | Hypothesis (1 line) | Key change | Public LB | Private LB | Keep? |
|---|------|---------------------|-----------|-----------|-----------|-------|
| — | —    | _(none yet)_        | —         | —         | (hidden until R1 end) | — |

## Running notes
- Always record the **config/seed** so a result is reproducible (`.claude/standards/reproducibility.md`).
- A submission without a written hypothesis is a wasted submission. Don't.
- Watch for **public-LB overfitting**: if a change helps public but is not business-justified, be suspicious — the private 30% may punish it.
- Track *which top-20% members change* between experiments, not just the score number — that's where the signal is.

## Detailed records
> Link full experiment write-ups here as they're created, e.g. `- [exp-001](./experiments/exp-001.md)`.

- **v1-internal** (2026-06-27, commit `6a42d0c`, SEED=42) — **NOT submitted; budget still 0/10.** Equation `(Rev−Cost)×(1−Risk)`, all terms rank-normalized to [0,1], unified eq + per-segment business-prior weights ([[framework-design]]; plan `.claude/plans/2026-06-27-framework-v1-scoring.md`; code `src/score.py` + `src/validation.py`). **Internal top-20% stability:** subsample 0.998, weight-perturbation 0.865 (±15% jitter); score Gini 0.138; top-20% mix lender 64.6% / revolver 24.6% / transactor 10.8%. **Integrity check:** no-breakdown cohort = 23.1% of pop but only 9.7% of the top-20% (the `f5`-saturation fallback is not over-promoting them). **Keep → next: calibrate weights (stage 6) before the first submission** — ~13% of the top-20% is weight-sensitive.
- **v1.1** (2026-06-27, stage-6 calibration) — **NOT submitted; budget still 0/10.** Halved `borrow_int` lender weight 0.80→0.40 (sensitivity: `f17`=line size drove 62% of top-20%; `src/calibrate.py`). Effect vs v1: 22.1% of top-20% changed (Spearman 0.957); top-20% rebalanced lender 64.6%→43.1% / revolver 24.6%→36.8% / transactor 10.8%→20.1%; borrow_int demoted #1→#4 lever. Stability held: subsample 0.998, weight-perturbation 0.836, Gini 0.123; no knife-edge term. **Current default weights** (`src/score.py`). **Next: LB-informed tuning deferred to post-submission-1.**
