# Framework v1 — Profitability Score Design

_Status: **DRAFTED 2026-06-27**, pending implementation. Living doc — update as calibration/validation
refine. Satisfies roadmap stage 5 (revenue−cost equation + business justification). Builds on the
research skeleton in [[research-findings]] and the decisions in [[decision-log]]._

## Master equation
```
score = ( Revenue − Cost ) × (1 − Risk)
```
- **One equation for all 500K** rows; the customer segment changes the *weights*, not the structure
  (decision: unified equation + per-segment weights).
- **Risk applied multiplicatively** on the whole (Rev−Cost) score (decision: shave the whole score).
- All term inputs are **rank-normalized to [0,1] percentiles** before combining — raw scales span ~6
  orders of magnitude (`f4` max 698K vs `f11` max 0.33), see [[feature-notes]].

## Segment tag — selects the weight column, does NOT split the data
| Segment | Rule | Share | Earns Amex money via |
|---|---|---|---|
| Lender | `f17` present (has borrowing line) | 41.5% | borrowing interest |
| Revolver | `f17` missing **and** `f1` > 0 | 26.5% | carried-balance interest |
| Transactor | `f17` missing **and** `f1` == 0 | 31.9% | interchange + fee only |

## Revenue terms — each a 0–1 rank, weighted sum
| Term | Input | Business reason |
|---|---|---|
| **Spending** | `rank(f6+f7+f8+f9+f10)` within has-breakdown group; `rank(f5)` within no-breakdown group; unified onto one 0–1 axis + `has_spend_breakdown` flag | Interchange revenue ≈ spend volume. **NOT** raw `f5` for the 77% — it's capped/saturated ([[assumptions]] A1). Cohort-rank fallback decision for the 23%. |
| **Balance interest** | `rank(f1)` | Interest on carried balances. Naturally 0 for transactors. |
| **Borrowing interest** | `has_lend_line · rank(f17)` | Interest on the lending line. **Drop `f18`** (r=0.92 with `f17`, redundant). |
| **Relationship depth** | small · `rank(f19 + f20)` | More cards → more spend + supplementary fees. |

## Cost terms — each a 0–1 rank, weighted sum, subtracted
| Term | Input | Business reason |
|---|---|---|
| **Rewards** | `rank(f21)` + λ·`rank(f4)`·(1 − `redemption_intensity`) | `f21` redeemed = booked cost; outstanding `f4` balance is a **contingent liability discounted by breakage** — members who rarely redeem carry a cheaper liability. `redemption_intensity = f21/(f4+f21)`. ([[decision-log]] f4-discount.) |
| **Perks** | `rank(benefit_burden)` from `f13,f14,f15,f16` | Lounge / airline / cab / entertainment credits Amex pays for. |
| **Servicing** | small · `f2` | Cancellation-call attrition signal. |

## Risk haircut
```
Risk  = clamp( a·rank(f11) + b·f3 , 0, <1 )
score = (Revenue − Cost) × (1 − Risk)
```
`f11` = PD-like default likelihood (cost-side multiplier); `f3` (collection-driven cancels) amplifies it.

## Per-segment weights — v1 = business priors (calibration is stage 6)
A 3-column weight table (transactor / revolver / lender) over the revenue+cost terms:
- **Transactor** → spending weighted highest; borrowing-interest 0; balance-interest low.
- **Revolver** → balance-interest weighted up; borrowing 0.
- **Lender** → borrowing-interest weighted up.

Concrete starting numbers set at implementation; documented + reproducible (fixed seed).

## Missing handling
A missing input means that revenue/cost **does not exist** for the member → it contributes **0**
(non-rewards member: 0 rewards cost; charge-only: 0 borrowing interest). Segment flags encode the rest.
Never fill-0 as a *value* — the 0-contribution is structural (MIA missingness-as-signal, [[decision-log]]).

## Output
A continuous profitability score per `id`, then ranked. **Only the top-20% overlap is graded.**

## Calibrated weights & sensitivity (v1.1 — stage 6, 2026-06-27)
Implemented `WEIGHTS` (transactor / revolver / lender), all term inputs in [0,1]:

| term | T | R | L |
|---|---|---|---|
| spending | 1.00 | 0.70 | 0.70 |
| balance_int | 0.00 | 0.80 | 0.40 |
| borrow_int | 0.00 | 0.00 | **0.00** (v1.2; was 0.40) |
| depth | 0.20 | 0.20 | 0.20 |
| rewards_cost | 0.50 | 0.40 | 0.40 |
| perks_cost | 0.30 | 0.30 | 0.30 |
| servicing_cost | 0.15 | 0.15 | 0.15 |

Risk: `× (1 − clamp(0.8·rank(f11) + 0.2·f3, 0, 0.9))`; rewards λ = 0.5.

**Stage-6 change:** `borrow_int` lender weight halved **0.80 → 0.40** (user-approved hedge). `f17` is lend-line
*size* (capacity), not interest *earned*; at 0.80 it drove **62%** of the top-20% (`src/calibrate.py`). Halving
demoted it from the #1 to the #4 lever (drop-churn 0.62 → 0.38) and rebalanced the top-20% from lender 64.6% →
43.1% (≈ the 41.5% population share), letting spend + carried-balance lead. Cost: 22.1% of the top-20% changed
vs v1 (Spearman 0.957).

**Per-term leverage (v1.1 — top-20% churn if dropped / under ±25% nudge):** spending .63/.22 · balance_int .54/.17
· rewards_cost .44/.12 · borrow_int .38/.11 · perks .25/.07 · depth .17/.05 · servicing .14/.03. **No knife-edge
term** (max ±25% churn .22). `depth`/`servicing` are near-negligible → candidates to drop for a simpler writeup.

**LB-informed calibration is now ACTIVE** (1/10 submitted, baseline 0.449; v1.2 calibrated below) — one
economically-justified lever per submission; do not grid-search a proxy or chase the public 70%. Diagnostics: `src/compare.py` (baseline agreement),
`src/llm_judge.py` (OpenAI judge — indifferent vs naive spend on contested pairs; cross-check only).

## v1.2 calibration (stage 9 — 2026-06-29, post-submission-1)
**Baseline sub-v1 (v1.1 weights) scored public-LB 0.449** (top-20% overlap; ≈2.25× random). Stage-9 research — 3 converging sources (internal $-decomposition of 500K, external Amex unit-economics from 10-K/regulatory filings, independent deep-research pass) — **zeroed `borrow_int` 0.40 → 0.00**: `f17` is lend-line SIZE, a capital cost (CECL provisioning + Basel III RWA), not revenue; lending profit is the carried balance `f1` (~9.6% net/$ — the highest per-$ margin lever). Hard zero chosen over a negative-unused-capacity penalty (v1.2b) — the latter over-penalizes a 2nd-order cost (idle line ≈ −0.3 to −0.5%/$) and adds an uncalibratable parameter (`scratchpad/measure_v12b.py`).

Effect vs v1.1: top-20% **churn 23.1%** (Spearman 0.913); segment mix lender 43.1%→**20.5%** / revolver 36.8%→**48.8%** / transactor 20.1%→**30.8%** (composition now tracks realized profit, not line ownership). Stability HELD: subsample 0.998, weight-perturb 0.825. Revenue capture: spend 2.1× / carried-balance 1.4× / lend-line **0.6×**. → `data/scores_v2.csv`, `submissions/submission_v2_zero-borrow.xlsx`. **RESULT: public-LB 0.465 (+0.016 vs v1's 0.449) — the lend-line fix improved top-20% overlap; direction confirmed.** NOTE: score-Gini is ill-posed for a signed index (don't cite it); use revenue-capture lift.

## Gap diagnosis & magnitude experiment (stage 9b — 2026-06-29)
Leaders sit at public-LB **~0.89–0.90**; our best is **0.465**. Both our submissions are PERCENTILE-based and clustered ~0.46 (Jaccard 0.62) → the percentile framework appears **ceilinged near 0.46**; the 0.44 gap is **structural, not a weights problem** (a one-lever tweak gave only +0.016).

**Hypothesis (framework v2.0):** rank by **dollar-magnitude** revenue−cost (NOT percentile), so natural dollar magnitudes weight the features like a real P&L. Impl `src/score_magnitude.py`; writeup `framework-doc-v3-magnitude.md`. dollar-profit = 0.022·spend + 0.08·f1 − 0.01·f21 − benefits − 0.5·f11·f1.

**framework-critic red-team (accepted, key points):** (1) for a SET-OVERLAP metric, magnitude-vs-rank matters ONLY insofar as it re-orders the cutoff — "our top-20% holds X% of margin" is **circular**, struck from the writeup; (2) FATAL `f5`-cap cohort collapse (23%→1.1% of top-20%) — FIXED by quantile-mapping `f5` onto the breakdown spend distribution (→24.8%, fair); (3) score was `f7`-dominated (0.90 var-share; the fix cut f7-overlap 0.75→0.46); (4) cost-per-point is a free parameter that flips ~20–40% of negative-margin signs (can't calibrate without a label).

**RESULT: v3 dollar-profit scored public-LB 0.614 (+0.149 over percentile v1.2's 0.465) — the magnitude bet WON; the ~0.46 percentile ceiling is broken.** Framework v2.0 (dollar-magnitude revenue−cost) is now our **best validated approach** and the new baseline. Still ~0.286 below leaders (~0.90) → refine WITHIN magnitude: calibrate cost-per-point + interest rate against LB feedback, test pure dollar-spend (v4) to isolate whether the cost/interest terms add value, re-add excluded terms (f4 contingent, f3). `src/score_magnitude.py` is the new primary engine; percentile `src/score.py` (v1.2, 0.465) retained as documented fallback.

## v1 simplifications — named ceilings, fixable later
1. **Risk shaves the whole score** → a rare risky-but-unprofitable member is nudged up slightly;
   irrelevant to the top-20% we're graded on. *Upgrade:* apply risk to credit-exposed revenue only.
2. **Weights are business priors**, not calibrated. *Upgrade:* stage 6 calibration — business-first;
   CRITIC/entropy/AMPI as a **cross-check only** (they reward statistical dispersion, not profit; the
   `logins`/`email_open` trap — see [[feature-notes]] warning).

## Validation before ANY submission (stage 7)
- Score all 500K, deterministic (fixed seed).
- **Top-20% stability**: bootstrap resample + weight perturbation → measure top-20% membership churn.
- **Label-free sanity**: Lorenz/Gini of the score; transactor/revolver/lender profiles plausible;
  top & bottom tail face-validity.
- **Revenue capture / top-quintile lift** (`src/validation.py:revenue_capture`, `spend_only_overlap`):
  the closest computable proxy for the graded top-20%-overlap metric — does our top-20% hold a
  disproportionate share of each raw revenue driver? (whale-curve concentration; ZILN/2304.03038 lift.)
- **No leaderboard submission until stability passes.** Protect the 10-submission budget.

### Baseline diagnostic readings (v1.1, full 500K — recorded 2026-06-28)
| metric | value | read |
|---|---|---|
| subsample top-20% stability (Jaccard) | 0.998 | tail is not a sampling artifact ✅ |
| weight-perturbation stability | 0.836 | robust to ±15% weight jitter ✅ |
| score concentration (Gini) | 0.123 | **flat** — all-percentile terms compress the dollar tail that real profit has ⚠ |
| top-20% capture: spend / f1 / f17 | 0.42 / 0.26 / 0.30 | lifts 2.1× / 1.3× / 1.5× — tilted to revenue, but modest |
| overlap vs naive spend-only top-20% | 0.341 | only ⅓ of our top-20% are top spenders — **flag for submission-#1 calibration** |

_Not a tuning trigger (numeric calibration still frozen until the submission-#1 signal, see above). These
are watch-items: the low spend overlap + flat Gini are the first things to interrogate once we have real
leaderboard feedback — interchange is the dominant lever for a charge-heavy premium card, so a 0.34 spend
overlap may mean balance/borrow terms are over-weighted relative to spend._
