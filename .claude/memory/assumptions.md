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

## Forbidden assumptions (never make these)
- That `id` may be used as a predictor.
- That missing = 0 without a stated reason.
- That overfitting the public 70% is safe (hidden 30% decides).
- That a high-accuracy black box is acceptable without business logic.
- That objective weighting (CRITIC/entropy/PCA) can set the framework weights — with no label they reward dispersion, not profit (they up-weight `logins`/`email_open`); use as cross-check only. See `feature-notes.md` EDA round 2.
