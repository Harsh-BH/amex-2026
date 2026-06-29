# Roadmap

_The plan. Update status as stages complete. Reflects the R1 lifecycle; R2/R3 sketched at the end._

## Round 1 — Profitability Framework (current)

| # | Stage | Workflow | Status | Exit criterion |
|---|---|---|---|---|
| 0 | Deep understanding | — | ✅ done | Problem explained, insights in memory. |
| 1 | `.claude` setup | `01-project-initialization` | ✅ done | Operating system in place. |
| 1b | Literature review (3 rounds) | — | ✅ done & CLOSED | ~70 papers verified (core + gap-fill + premium-card/rewards/label-free-validation). **Round-3 verdict: diminishing returns → build next.** [[research-findings]], [[bibliography]], `reports/literature-review-r1-profitability.md`. SS dead (HTTP 402). |
| 2 | Environment | `02-environment-setup` | ✅ done | `.venv` (py3.14): pandas 3.0.3 / numpy 2.5.0 / openpyxl 3.1.5; reads 500K×24 in ~28s; pinned in `requirements.txt`. Run via `.venv/bin/python`. |
| 3 | EDA | `05-exploratory-data-analysis` | ✅ done | Distributions/correlations/missingness in `feature-notes.md`; f5-saturation + CRITIC-trap findings logged. |
| 4 | Missing-value strategy | `06-data-cleaning` | ✅ done | Missing → 0-contribution + segment flags (no impute); baked into `src/score.py`. |
| 5 | Framework design | `09-framework-design` | ✅ done | v1 `(Rev−Cost)×(1−Risk)`, unified eq + per-segment weights; spec [[framework-design]], impl `src/score.py`. |
| 6 | Weight calibration | `10-weight-calibration` | 🟡 internal | v1.1: `borrow_int` hedged 0.80→0.40 (sensitivity `src/calibrate.py`); no knife-edge weights; weight table+sensitivity in [[framework-design]]. **LB-informed tuning deferred to post-submission-1.** |
| 7 | Score + validate | `11-evaluation` | ✅ done | 500K scored (`data/scores_v1.csv`); top-20% stability 0.998 subsample / 0.865 weight-perturb (`src/validation.py`). |
| 8 | First submission | `13-submission-generation` | ✅ done | sub-v1 uploaded 2026-06-29 → **public LB 0.449** (top-20% overlap; ≈2.25× random). Budget 1/10. |
| 9 | Iterate (≤10) | `12-leaderboard-improvement` | 🟡 active | sub-v1 0.449 → sub-v2 (zero borrow_int) **0.465** (+0.016). Budget 2/10. Next: tighten f4 rewards-liability (#3); guard public-70% overfit. |
| 10 | Document & finalize | `14-documentation` / `15-final-review` | ⬜ | Framework sheet complete; final-delivery checklist green. |

## Beyond R1
- **R2 — Elevating the Premier Card Experience** (case study). Reuse business-context + feature insights.
- **R3 — Deck submission & presentation.** Reuse documentation templates + experiment history as evidence.

## Open questions to resolve early
- Env fix for pandas/openpyxl (or commit to stdlib reader).
- Confirm `Prediction` column accepts continuous floats (A9).
- Direction/treatment of `f7` negatives and `f11` risk score (A5, A6).
