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

## Card reward economics (product brief Page 8 — AUTHORITATIVE, not a guess)
- **Reward multipliers: 5x points on flights/airline (`f6`) & prepaid hotels/lodging (`f9`); 1x on ALL other purchases (incl. `f7` other, `f8` entertainment, `f10` DINING).** 1 point ≈ 1–2¢ member value (issuer cost lower).
- ⇒ **Only airline (`f6`) + lodging (`f9`) are reward-expensive → the only net-NEGATIVE spend categories.** `f7`/`f8`/`f10` are all 1x → mildly net-POSITIVE and ~EQUAL. **This CORRECTS A13 and v5/v7/v8: dining (`f10`) is NOT a bonus category** — v5/v7 weighted it as the single TOP-positive margin (+0.0185 > other's +0.013), which contradicts the 1x structure; it should ≈ `f7`/`f8`. (v10's triangulation made `f10` *negative* — also unsupported by the terms; likely a member-correlation artifact, not reward economics.)
- **Lifestyle credits (annual $ = benefit COSTS):** cabs `f15` $150-250 (**"$15/mo + $20 Dec" → CONFIRMS `f15` is MONTHS; cost ≈ $15/mo, so the code adding raw `f15` understates it ~15×**); airline credit `f14` $150-250 (matches f14 max 200); digital-ent credit `f16` $180-280; + fitness/clothing/commerce credits (no f-code). Lounge `f13` (cardholder+2 guests). NB benefit costs barely move the top-20% (triangulation: small/unstable).
- **No preset limit (charge card) + Plan It installments + lend line** ⇒ revolving balance `f1` interest is real revenue — supports v10's `f1` up-weight. Welcome bonus 80–150K pts; annual fee $500–750 constant (A7, not a differentiator).

## Structured missingness clusters (treat together)
- `f6`–`f10` (115,698) · `f4`+`f21` (257,228) · `f13`–`f16` (13,716) · `f17`/`f18` (~60%) · `f23` (88%)

## EDA findings (2026-06-27, `src/eda.py` + `notebooks/eda.ipynb`)
- **A1 hard-confirmed + quantified:** Σ(category spends `f6`–`f10`) ≈ mean **48.6K** (max 240.8K) vs `f5` "Total Spend" mean **3.5K** (max 13.6K) — ~14× apart. `f5` is NOT total spend in category units (scaled/monthly/different metric). Use the category spends for true volume; never set `f5 = Σf6..f10`.
- **Segments:** lender (has `f17`) 41.5% · transactor/charge-only (`f17` missing, `f1`=0) 31.9% · revolver-no-lend 26.5%. **Transactors** = lowest risk (`f11`≈0.006), highest rewards balance (`f4`≈164K), highest cancel (`f2`≈0.236). **Revolvers** = highest revolve (`f1`≈5198) & risk (≈0.059), lowest cancel (0.08). → segment-aware scoring is real here.
- **Top-20% by spend skews LOW risk** (`f11` 0.02 vs 0.04, ratio 0.63), fewer collection calls (0.75×) and *fewer* logins (0.87×) — high spenders are low-risk, low-maintenance. Risk is not strongly adversarial at the spend-top (but is across segments).
- **⚠ Choice of spend anchor reshapes the scored top-20%.** Top-20%-by-`f5` is *weak*: its members are only ~1.0–1.5× the rest on every dimension except f5 itself (5.24×) — f5 is capped (~13.6K) and saturated, so it barely separates the tail. Top-20%-by-`f7` is *strong*: 7.2× f7, 3.2–4.4× all other spend cats, 2.2× `f4`, 2.4× `f21`, **0.27× risk, 0.17× cancel_calls**. → The real "whale" tail lives in the category spends (`f7`-dominant), not `f5`. Build volume from `f6`+`f7`+`f8`+`f9`+`f10`; anchoring on `f5` would mis-rank the only region the metric scores.
- **Collinearity:** `f17`~`f18` r=0.90 (redundant lend lines → combine/drop one); spend cats `f6`~`f9`, `f7`~`f10`, `f8`~`f10` r=0.6–0.7 → CRITIC-style deflation warranted.
- **Breakage signal:** `redemption_intensity = f21/(f4+f21)` mean ≈0.36 over rewards members → large unredeemed balances ⇒ `f4` cost discount justified.
- **Derived features built (21):** flags `has_lend_line`/`is_rewards_member`/`has_spend_breakdown`/`is_revolver`; ratios `redemption_intensity`/`benefit_burden`/`spend_diversity`/`engagement`/`revolve_to_lend`/`net_spend`; + percentile `*_rank` of 11 heavy-tailed features. In `add_features()`.

### EDA round 2 (weights / concentration / Spearman — `eda.weights()/concentration()/plot_*`)
- **CRITIC/entropy weights** (on rank-normalized feats): fairly flat (0.016–0.060 — rank-norm equalizes variance, so CRITIC differentiates by *redundancy*). Top objective weight: `total_spend`, `logins`, `email_open`, `cab_months`, `ent_credit`. Bottom (deflated — redundant/sparse): `email_click` (88% missing), `collect_calls`, `consumer_lend`, `lend_line`. → an equal-weight baseline is reasonable; CRITIC mainly down-weights the collinear lend pair + dead `email_click`.
- **⚠ Do NOT let CRITIC/entropy drive the framework weights.** There is no profitability label, so these measure statistical *dispersion/redundancy*, not P&L relevance — that's why `logins` and `email_open` (near-zero profit content) float to the top while `lend_line`/`rewards` sink. Using them as primary weights = the §17 failure mode (high score, no defensible business logic). Weights come from revenue−cost reasoning first; objective weights are a sanity cross-check only.
- **Gini concentration:** `revolve_bal` **0.80** (most concentrated — few big revolvers), `lodge_spend`/`ent_spend`/`rewards_redeemed` 0.72–0.76, spend cats 0.62–0.76, `total_spend` only **0.55**, lend lines lowest **~0.40**. High-Gini revenue features separate the top-20% tail best (research §N).
- **Spearman > Pearson** for spend cats (0.61–0.71) and lend pair (0.92) — monotonic structure is stronger than linear; use Spearman for collinearity decisions. `correlations()`/`plot_corr()` now default to Spearman.

### EDA round 3 (gap diagnosis 2026-06-29 — why v7=0.768 vs leaders 0.90)
- **No-breakdown cohort = the #1 ceiling.** 75,174 members (15% of pop) have neither spend breakdown nor `f4` → v7 ranks them by interest `f1` only (38% have `f1`=0 too → near-random). A linear imputation of category-sum spend from `f4`+`f21`+`f13–f16`+`f11` reaches **OOS Spearman 0.527 vs `f4`'s 0.282** ([[assumptions]] A15). `f5` confirmed useless (0.009).
- **`f15` is MONTHS not dollars** (0–11). The benefits term adds it as dollars → cab cost understated ~15×. Fixing (×~$15/mo) reshuffles only ~3.3K top-20% members (Spearman 0.987 — modest). Rescale or drop.
- **`f3`=1 contamination:** 6,662 collection-flagged members in v7's top-20% (mean spend $392, risk 0.171 = ~5–10×) — interest revenue beats `exp_loss` (A17).
- **`f19`/`f20` NEGATIVELY correlated with spend** (`f19` Spearman −0.214 within breakdown) — do NOT use as a revenue multiplier (A18).
- **Score ≈ rank by `f7`.** `f7` = 54% of score variance; in the breakdown top-20% `f7` is 114.8% of catrev (`f6`+`f9` negative margins dig a −$33M hole). Both catrev and interest (`0.08·f1`) differentiate the tail (std ≈2.4× higher inside top-20%); `exp_loss`/benefits barely move the cutoff. Cutoff is NOT knife-edge (1.7% straddle).
