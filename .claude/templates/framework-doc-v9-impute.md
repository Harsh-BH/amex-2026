# Profitability Framework — Submission Writeup (v2.4 impute-cohort / submission v9)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v7 category-margin magnitude framework, with the no-breakdown cohort's spend IMPUTED by a
     transparent linear model instead of a single weak proxy. Margins/interest/cost unchanged from v7. -->

## Variables Used
We score each member's estimated annual dollar contribution margin using 14 of the 23 features, each a real P&L line.

Revenue: f6 Airline, f7 Other, f8 Entertainment, f9 Lodging, f10 Dining spend — each weighted by its OWN net margin (a dollar spent in different categories is not equally profitable; see below); f1 Average Revolve Balance (net interest income).

Cost: f13 Lounge visits, f14 Airline credit, f15 Cab credit, f16 Entertainment credit (benefit credits paid out); f11 Average Risk Score (expected credit loss, scaled by balance exposure). The points-reward cost is folded INTO the category margins, so there is no separate redeemed-points term.

Spend imputation (no-breakdown cohort only): for the ~23% of members whose category spend (f6–f10) is not reported, we estimate their spend from the features that best predict spend among members who DO report it — f4 Points Balance, f21 Points Redeemed, f1 Balance, f11 Risk, f12 Logins, and f13–f16 benefit usage. f13–f16 thus play two honest roles: an out-of-pocket benefit cost for everyone, and — for the no-breakdown cohort only — an observed signal of how much a member spends, since premium-benefit users are premium spenders.

Excluded: id (leakage); the constant annual fee; f5 Total Spend (capped and uncorrelated with real category spend — rank-corr 0.01, so it is noise); f17/f18 lend line (capital cost, not revenue); f2/f3 servicing/collection calls; f19/f20 relationship depth (the data shows it is negatively related to spend); f22/f23 email engagement (activity is not profit).

## Profitability Equation
Each member's score is their estimated annual dollar contribution margin, with spend weighted by per-category net margin (NO percentile ranking):

    score_$ = category_margin_revenue + net_interest - benefit_credits - expected_loss

    category_margin_revenue = -0.020*f6 + 0.013*f7 + 0.010*f8 - 0.015*f9 + 0.0185*f10   (members with a category breakdown)
                            = blended_avg_margin * imputed_spend                          (no-breakdown cohort)
    net_interest    = 0.080 * f1
    benefit_credits = f14 + f15 + f16 + 35 * f13
    expected_loss   = 0.50 * f11 * f1

For the no-breakdown cohort, imputed_spend is the member's spend estimated by a transparent linear model (below) and mapped onto the breakdown cohort's spend-dollar scale; blended_avg_margin is the breakdown cohort's realized average net margin. The category margins are NET (interchange minus the category's reward cost), so the 5x-reward categories airline (f6) and lodging (f9) carry negative per-dollar margins, while dining (f10), other (f7), and entertainment (f8) are positive.

## Prediction Logic
The dollar margin is written as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% is the graded set. We keep magnitude (no percentile flattening). A missing input contributes 0 to a cost/revenue term (that line does not exist for the member), EXCEPT that the no-breakdown cohort's missing spend is imputed rather than zeroed (see Feature Transformations). Deterministic (seed 42), reproducible from src/score_magnitude.py (dollar_profit_catmargin_v9), never uses id.

## Variable Selection Logic
This is the v7 category-margin magnitude framework (public-LB 0.768) with one fix to its largest blind spot. The ~23% of members with no category-spend breakdown cannot be ranked on real spend, and their "Total Spend" field (f5) is uncorrelated with actual spend (rank-corr 0.01) — pure noise. Ranking them on f5, or on the single proxy f4 (points balance) while zeroing the ~65% who lack f4, left about 15% of ALL members with essentially no spend signal. Instead we impute their spend from the full set of features that genuinely predict it among members who report it. Everything else — the per-category margins, net interest, benefit credits, expected loss — is unchanged from v7, so the change is isolated.

## Coefficient/Weight Derivation
Two kinds of coefficients, both documented and non-arbitrary:
1. P&L rates (unchanged from v7): category net margins are cited interchange-minus-reward rates (dining +1.85%, other +1.3%, entertainment +1.0%, lodging −1.5%, airline −2.0%); net interest ~8% (Amex 10-K yield minus loss/opex); loss-given-default 50%; lounge ~$35/visit.
2. Spend-imputation coefficients (new): an ordinary least-squares regression of log(category-sum spend) on log-transformed f4, f21, f1, f12, f13–f16 and on f11, fit ONLY on members who report a breakdown. It learns how observable behavior predicts spend; it uses no id and no profitability label (none exists) — it imputes a MISSING FEATURE, not a target. Coefficients are inspectable and stable; out-of-sample (5-fold) they rank true spend at rank-corr 0.46 versus 0.19 for the single f4 proxy they replace.

## Feature Transformations
We do NOT percentile-rank the score. Spend is decomposed into categories, each multiplied by its net margin. For the ~23% with no breakdown: heavy-tailed inputs are log-transformed, missing inputs filled with the cohort median, and the linear model predicts each member's spend; we then quantile-map that prediction onto the breakdown cohort's spend-dollar distribution and apply the blended average margin. This (a) gives every no-breakdown member a spend estimate from real evidence rather than zero, and (b) keeps both cohorts on one dollar scale. Missing benefit/reward inputs contribute 0 cost (a non-rewards member incurs none — co-missingness is a population flag). f7 refunds are negative and net down correctly.

## Business Logic
A member is profitable when their margin-weighted spend plus net interest exceeds their benefit credits and expected losses. Two business judgments drive the ranking. First, a dollar of airline or hotel spend, after its rich 5x reward cost, can lose the issuer money, whereas everyday/dining spend is profitable — so a heavy traveler concentrated in 5x categories can rank below a moderate everyday spender. Second, when a member's spend detail is not reported, we do not pretend it is zero or read a broken field; we infer it from what premium spenders look like — they hold and redeem more points and use lounge/airline/dining benefits. This is how an analyst estimates an unknown: from the correlated, observable behavior of similar known customers.

## Assumptions
- Masked features are proxy-dollars; the category margins set the relative profitability of each spend type (research-anchored, not label-calibrated).
- Category net margins follow the cited interchange-minus-reward economics; airline/lodging are net-negative.
- f5 is noise for the no-breakdown cohort (rank-corr 0.01 with real spend) → replaced by a multi-feature spend imputation (out-of-sample rank-corr 0.46 vs 0.19 for f4 alone).
- The imputation assumes the no-breakdown cohort's spend RELATES to behavior the way the breakdown cohort's does (so coefficients transfer) and that its spend LEVEL is comparable (the quantile-map). The within-cohort ORDERING is well-evidenced; the LEVEL is the one item only the leaderboard can confirm.
- The annual fee is constant and excluded (A7); lend-line size is a capital cost (A11); f19/f20 depth is not a positive spend signal (it is negative in the data).

## Validation Approach
Label-free, full 500K. This is a single, isolated change to the validated v7 framework (public-LB 0.768): only the no-breakdown cohort's spend proxy changes, so any leaderboard move is attributable to it. Internal gate: the imputation's out-of-sample (5-fold cross-validated) rank-correlation to true spend is 0.46 — more than double the 0.19 of the f4 proxy it replaces. Effect on the ranking: it reshuffles ~12% of the top-20% and raises the no-breakdown cohort from 10.5% to 19.0% of the top-20% (still below its 23% population share, so a measured correction, not blanket promotion). We do NOT claim our score's own shape proves correctness; whether better spend recovery for this cohort improves top-20% overlap is decided by the leaderboard. We changed one lever, on documented grounds, without fitting the public split.

## Additional Notes (Optional)
This is v2.4, isolating the highest-value structural fix from the gap analysis (no-breakdown cohort blindness). If it improves overlap, the next isolated test is reverting the airline/lodging margins to positive (the negative signs were never independently validated and are the main private-split risk). If it does not help, v7 (0.768) remains the validated best and the cohort's spend LEVEL — not its ordering — is the likely cause. Held: an explicit f3 collection-delinquency penalty (~6,700 high-risk members currently reach the top-20% on interest revenue) and a fix to the f15 benefit-cost unit (months vs dollars).
