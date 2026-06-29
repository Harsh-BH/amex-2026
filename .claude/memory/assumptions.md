# Assumptions Register

_Every assumption we rely on. Status: ✅ verified · ⚠ unverified · ❌ disproven. Re-check before trusting._

| # | Assumption | Status | Evidence / Action |
|---|---|---|---|
| A1 | `f5` "Total Spend" is **NOT** the sum of `f6`–`f10` | ✅ | `f5` max ≈13,596 but `f7` max ≈146,701. Different scale/definition. Do not assume additivity. |
| A2 | `f6`–`f10` (category spends) are missing **together** for the same 115,698 rows | ✅ | Identical missing counts across all five in the 500K scan. Likely "no category breakdown" segment. |
| A3 | `f4` (rewards balance) & `f21` (redeemed) co-miss for the same 257,228 rows | ✅ | Identical missing counts → a "rewards population" flag. |
| A4 | `f17`/`f18` missing (~58/62%) = charge-only members with no lend line | ⚠ | Plausible; confirm distribution vs revolve `f1`. |
| A5 | `f11` is a probability-of-default-like risk score (higher = riskier = cost) | ⚠ | Range 0–0.326, mean 0.034. Confirm monotonic direction in EDA. |
| A6 | `f7` negatives are refunds/returns (legitimate, keep sign) | ⚠ | Min −274.6. Decide treatment (floor at 0? net?) in framework design. |
| A7 | Annual fee is constant within Premier → not a ranking feature | ✅ | Stated by product overview; fee is product-level. |
| A8 | Ground truth profitability ≈ a revenue−cost formula on these (or richer) features | ⚠ | Inference from problem design; validated only via leaderboard. |
| A9 | `Prediction` should be a continuous profitability score (rank-ordered), not a 0/1 flag | ⚠ | Metric ranks our values to cut top-20%; continuous is safer. Confirm template accepts floats. |
| A10 | Tenure / Bureau score / Size-of-Wallet (slide 9) are **absent** from the 23 features | ✅ | Dictionary has only `f1`–`f23`; slide is illustrative. |
| A11 | `f17`/`f18` line SIZE is a **capital COST, not revenue** (unused line: $0 income, but CECL provisioning + Basel III RWA capital drag ≈ −0.3 to −0.5%/$) | ✅ | **3-source convergent** (internal + external + Gemini 10-K analysis). Lending profit is the carried balance `f1` (`balance_int`), NOT the line. → `borrow_int` should be **0 or negative**, not +0.40. v1.2 zeroes it. Stage-9 2026-06-29. |
| A13 | Spend-category net margins are **asymmetric; airline `f6` & lodging `f9` are net-NEGATIVE** (5x reward cost ~4.5% > MDR ~2.5–3%); dining `f10` & other `f7` net-positive | ⚠ | Cited MDR/reward rate cards (Gemini). Summing `f5`/`f6`–`f10` mixes profit+loss. But internal test: margin-weighting re-ranks <7% of top-20% (Spearman 0.998). Writeup-relevant; low ranking impact. |
| A12 | Amex rewards **breakage is LOW** (~3–4%; Membership-Rewards URR ≈96%) | ⚠ | Cited (Amex MR liability disclosure). **Contradicts the generic 17–18% breakage prior** — `f4` points balance is a near-FULL liability, not 80–90% discounted. Tighten the `f4` discount for Amex. Stage-9. |

## Forbidden assumptions (never make these)
- That `id` may be used as a predictor.
- That missing = 0 without a stated reason.
- That overfitting the public 70% is safe (hidden 30% decides).
- That a high-accuracy black box is acceptable without business logic.
- That objective weighting (CRITIC/entropy/PCA) can set the framework weights — with no label they reward dispersion, not profit (they up-weight `logins`/`email_open`); use as cross-check only. See `feature-notes.md` EDA round 2.
