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
| borrow_int | 0.00 | 0.00 | **0.40** |
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

**LB-informed calibration is still PENDING** (0/10 submissions, no label) — numeric tuning waits for the
submission-#1 signal; do not grid-search a proxy. Diagnostics: `src/compare.py` (baseline agreement),
`src/llm_judge.py` (OpenAI judge — indifferent vs naive spend on contested pairs; cross-check only).

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
- **No leaderboard submission until stability passes.** Protect the 10-submission budget.
