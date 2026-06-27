# Feature Notes — `f1`–`f23`

_Per-feature meaning, stats (from a full 500K scan, 2026-06-26), P&L role, and modeling notes.
Direction: (+) revenue/value · (−) cost/risk · (±) ambiguous. Update as EDA refines._

| Feat | Meaning | Min | Max | Mean | Missing | Role | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Identifier | 0 | 499,999 | — | 0 | 🚫 | **NEVER use as predictor.** |
| `f1` | Avg Revolve Balance 12m | 0 | 17,968 | 2,467 | 0 | ± | Interest revenue but credit-risk signal. |
| `f2` | Cancellation Calls 12m | 0 | 1 | 0.17 | 0 | − | Attrition signal (~17%). Binary. |
| `f3` | Cancel Calls due to Collection | 0 | 1 | 0.11 | 0 | − | Delinquency/credit-risk (~11%). Binary. |
| `f4` | Rewards Points Balance | 2 | 697,899 | 126,607 | 51% | ± | Liability + engagement. Co-misses with `f21`. |
| `f5` | **Total** Spend 12m | 0 | 13,596 | 3,465 | 6,340 | + | ⚠ NOT sum of `f6`–`f10` (scale differs). |
| `f6` | Airlines Spend 12m | 0 | 52,198 | 10,032 | 23% | + | 5x category. Co-misses `f6`–`f10`. |
| `f7` | Other Spend 12m | **−275** | 146,701 | 30,822 | 23% | + | Largest category. **Negatives = refunds.** |
| `f8` | Entertainment Spend 12m | 0 | 9,420 | 1,523 | 23% | + | |
| `f9` | Lodging Spend 12m | 0 | 10,829 | 1,652 | 23% | + | 5x prepaid-hotel category. |
| `f10` | Dining Spend 12m | 0 | 21,651 | 4,536 | 23% | + | |
| `f11` | Avg Risk Score 12m | 0 | 0.326 | 0.034 | 2,510 | − | PD-like; higher = expected loss. |
| `f12` | Website Login Counts | 0 | 116 | 31 | 25,005 | ± | Engagement vs servicing/complaints. |
| `f13` | Lounge Access Count | 0 | 3 | 0.48 | 13,716 | − | Benefit cost (+engagement). Co-misses `f13`–`f16`. |
| `f14` | Airline Credits used | 0 | 200 | 43 | 13,716 | − | Benefit cost (fee credit). |
| `f15` | Cab benefits usage (months) | 0 | 11 | 4.0 | 13,716 | − | Benefit cost. |
| `f16` | Entertainment Credit Used Amt | 8.9 | 64.4 | 53.4 | 13,716 | − | Benefit cost (non-zero floor ≈8.9). |
| `f17` | Total Lend Line Amount | 1,000 | 63,800 | 24,165 | 58% | ± | Lending capacity → interest + risk. |
| `f18` | Total Consumer Lend Line | 1,000 | 54,800 | 21,976 | 62% | ± | Subset of `f17`. |
| `f19` | # Supplementary Accounts | 1 | 4 | 1.80 | 22 | + | More cards → spend + supp fees. |
| `f20` | # Active Charge Cards | 1 | 2 | 1.19 | 101 | + | Relationship depth. |
| `f21` | Rewards points redeemed 12m | 0 | 365,166 | 62,730 | 51% | ± | Realized rewards cost + engagement. |
| `f22` | Emails Opened 6m | 0 | 15 | 4.58 | 94,654 | + | Engagement. |
| `f23` | Emails Clicked 6m | 1 | 3 | 1.31 | 88% | ± | Engagement, but ~88% missing → weak. |

## Category mapping (from problem slide 9)
- **CM spend & balance:** `f1`, `f5`–`f10`
- **Benefit usage:** `f13`–`f16`
- **Engagement:** `f2`, `f12`, `f19`, `f22`, `f23`
- **Profile / risk:** `f3`, `f11`, `f17`, `f18`, `f4`, `f21`

## Structured missingness clusters (treat together)
- `f6`–`f10` (115,698) · `f4`+`f21` (257,228) · `f13`–`f16` (13,716) · `f17`/`f18` (~60%) · `f23` (88%)

## EDA findings (2026-06-27, `src/eda.py` + `notebooks/eda.ipynb`)
- **A1 hard-confirmed + quantified:** Σ(category spends `f6`–`f10`) ≈ mean **48.6K** (max 240.8K) vs `f5` "Total Spend" mean **3.5K** (max 13.6K) — ~14× apart. `f5` is NOT total spend in category units (scaled/monthly/different metric). Use the category spends for true volume; never set `f5 = Σf6..f10`.
- **Segments:** lender (has `f17`) 41.5% · transactor/charge-only (`f17` missing, `f1`=0) 31.9% · revolver-no-lend 26.5%. **Transactors** = lowest risk (`f11`≈0.006), highest rewards balance (`f4`≈164K), highest cancel (`f2`≈0.236). **Revolvers** = highest revolve (`f1`≈5198) & risk (≈0.059), lowest cancel (0.08). → segment-aware scoring is real here.
- **Top-20% by spend skews LOW risk** (`f11` 0.02 vs 0.04, ratio 0.63), fewer collection calls (0.75×) and *fewer* logins (0.87×) — high spenders are low-risk, low-maintenance. Risk is not strongly adversarial at the spend-top (but is across segments).
- **Collinearity:** `f17`~`f18` r=0.90 (redundant lend lines → combine/drop one); spend cats `f6`~`f9`, `f7`~`f10`, `f8`~`f10` r=0.6–0.7 → CRITIC-style deflation warranted.
- **Breakage signal:** `redemption_intensity = f21/(f4+f21)` mean ≈0.36 over rewards members → large unredeemed balances ⇒ `f4` cost discount justified.
- **Derived features built (21):** flags `has_lend_line`/`is_rewards_member`/`has_spend_breakdown`/`is_revolver`; ratios `redemption_intensity`/`benefit_burden`/`spend_diversity`/`engagement`/`revolve_to_lend`/`net_spend`; + percentile `*_rank` of 11 heavy-tailed features. In `add_features()`.
