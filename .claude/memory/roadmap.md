# Roadmap

_The plan. Update status as stages complete. Reflects the R1 lifecycle; R2/R3 sketched at the end._

## Round 1 — Profitability Framework (current)

| # | Stage | Workflow | Status | Exit criterion |
|---|---|---|---|---|
| 0 | Deep understanding | — | ✅ done | Problem explained, insights in memory. |
| 1 | `.claude` setup | `01-project-initialization` | ✅ done | Operating system in place. |
| 1b | Literature review (3 rounds) | — | ✅ done & CLOSED | ~70 papers verified (core + gap-fill + premium-card/rewards/label-free-validation). **Round-3 verdict: diminishing returns → build next.** [[research-findings]], [[bibliography]], `reports/literature-review-r1-profitability.md`. SS dead (HTTP 402). |
| 2 | Environment | `02-environment-setup` | ✅ done | `.venv` (py3.14): pandas 3.0.3 / numpy 2.5.0 / openpyxl 3.1.5; reads 500K×24 in ~28s; pinned in `requirements.txt`. Run via `.venv/bin/python`. |
| 3 | EDA | `05-exploratory-data-analysis` | ⬜ | Distributions, correlations, missingness map recorded in `feature-notes.md`. |
| 4 | Missing-value strategy | `06-data-cleaning` | ⬜ | Documented imputation/flag rule per cluster (A2–A4). |
| 5 | Framework design | `09-framework-design` | ⬜ | Revenue−cost equation drafted with business justification. **Direction set by [[research-findings]]: `[Rev−Cost]×(1−loss(risk))`, risk-discount multiplicative, transactor/revolver split.** |
| 6 | Weight calibration | `10-weight-calibration` | ⬜ | Weights/normalization set; sensitivity checked. |
| 7 | Score + validate | `11-evaluation` | ⬜ | All 500K scored; top-20% stability checked across resamples. |
| 8 | First submission | `13-submission-generation` | ⬜ | Template-valid file; experiment logged; baseline public LB. |
| 9 | Iterate (≤10) | `12-leaderboard-improvement` | ⬜ | Hypothesis-driven improvements; private-overfit guarded. |
| 10 | Document & finalize | `14-documentation` / `15-final-review` | ⬜ | Framework sheet complete; final-delivery checklist green. |

## Beyond R1
- **R2 — Elevating the Premier Card Experience** (case study). Reuse business-context + feature insights.
- **R3 — Deck submission & presentation.** Reuse documentation templates + experiment history as evidence.

## Open questions to resolve early
- Env fix for pandas/openpyxl (or commit to stdlib reader).
- Confirm `Prediction` column accepts continuous floats (A9).
- Direction/treatment of `f7` negatives and `f11` risk score (A5, A6).
