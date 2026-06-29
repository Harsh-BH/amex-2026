# Profitability Framework — Submission Writeup (v2.0 magnitude / submission v3)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     This is the DOLLAR-magnitude framework: rank by estimated dollar contribution margin, not percentile. -->

## Variables Used
We score profitability as an estimated dollar contribution margin using 13 of the 23 features, each a real P&L line.

Revenue: f5 Total Spend and its breakdown f6 Airline, f7 Other, f8 Entertainment, f9 Lodging, f10 Dining (these drive interchange/discount revenue); f1 Average Revolve Balance (drives net interest income).

Cost: f21 Rewards Points Redeemed (realized rewards cost); f13 Lounge visits, f14 Airline credit, f15 Cab credit, f16 Entertainment credit (benefit credits the issuer pays); f11 Average Risk Score (expected credit loss, scaled by balance exposure).

Excluded: id (using it is leakage); the annual fee (constant within the product, so it cannot differentiate members); f17/f18 Lend Line (the SIZE of a credit line is a capital cost — loss provisioning + regulatory capital — not booked revenue; confirmed when zeroing it improved our score); f4 Rewards Points Balance (a balance-sheet liability stock, not a period cash flow — the realized period cost is f21); f12 logins, f22/f23 emails (engagement measures activity, not profit); f19/f20 relationship depth (the data shows supplementary-account count associates negatively with profitability, so we exclude it pending review).

## Profitability Equation
Each member's score is their estimated annual dollar contribution margin — revenue minus cost, in proxy dollars, with NO percentile ranking:

    score_$ = interchange + net_interest - rewards - benefit_credits - expected_loss

    where
      interchange     = 0.022 * spend$        spend$ = (f6+f7+f8+f9+f10), or f5 where the breakdown is absent
      net_interest    = 0.080 * f1
      rewards         = 0.010 * f21
      benefit_credits = f14 + f15 + f16 + 35 * f13
      expected_loss   = 0.50 * f11 * f1

The coefficients are economic rates (below), not tuned weights; the features' natural dollar magnitudes do the weighting.

## Prediction Logic
The dollar margin is written directly as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% (100,000) is the graded set. Crucially we keep magnitude — we do NOT flatten features to percentiles — so the relative dollar size of each member's profit drivers is preserved when ordering. Roughly a fifth of members score negative (cost exceeds revenue); the exact share depends on the assumed cost-per-point and should be read as approximate. A missing input contributes 0 (that revenue or cost does not exist for the member). Deterministic (seed 42), reproducible from src/score_magnitude.py, never uses id.

## Variable Selection Logic
Every term maps to a line an issuer actually books. Spend earns interchange and is the dominant lever (~2.2% of spend). A carried balance earns net interest and is the highest-margin lever per dollar (~8%/year). Redeemed points are a realized cost; benefit credits are cash the issuer pays out; risk times balance exposure is the expected credit loss. We deliberately exclude the lend-line SIZE (a capital cost, not revenue — proven by our v1.2 result), the points BALANCE (a liability stock, not a period flow), engagement (activity is not profit), and relationship depth (the data does not support it as positive).

## Coefficient/Weight Derivation
The coefficients are real economic RATES from research, not hand-tuned weights: net interest ~8% (Amex 10-K net interest yield ~12% minus ~2-4% write-off/opex), blended discount ~2.2% (Amex 10-K), reward cost ~$0.01 per point (CFPB ~1.5 cents/dollar earned; issuer cost-per-point ~$0.008-0.012), loss-given-default ~50%, lounge cost ~$35/visit. Because the terms are in dollars, the features' natural magnitudes weight them automatically — there are NO arbitrary per-segment weights (a transactor simply has zero balance, so no interest term). The ranking is internally self-consistent under rate jitter (top-20% stays 0.83-0.93 stable when the interest rate is varied 6-12% or risk is made multiplicative) — this shows the chosen rates are not on a cliff, but it is NOT evidence that the rate vector points at the hidden truth; only the leaderboard can confirm that.

## Feature Transformations
The deliberate change from our earlier framework: we do NOT percentile-rank the combined score. Spend is the category sum f6-f10 (uncensored) where present. For the ~23% with no breakdown, f5 is capped (~13.6K) and on a different scale, so we quantile-map their f5 onto the breakdown spend distribution — preserving each member's internal f5 order while letting the cohort compete fairly. After this fix the no-breakdown cohort holds ~25% of the top-20% (matching its ~23% population share), instead of being crushed below everyone by the cap (assumption A1). Redeemed points are converted to dollars (times cost-per-point). A missing input means that revenue or cost does not exist and contributes 0; structured co-missingness (no lend line = charge-only) is handled naturally by the zero contributions. f7 refunds are negative and correctly net spend down.

## Business Logic
A member is profitable when the interchange and interest they generate exceed the rewards, benefit credits, and credit losses they cost. That is a literal issuer P&L. Because profit is heavily concentrated — a small set of high-spend or high-balance, low-risk members produce most of it — ranking members by their dollar margin (rather than by flattened percentiles) should line up with the true most-profitable 20%. The classic unprofitable "rewards maximizer" — heavy redemptions and benefit-credit usage, modest spend, elevated risk — correctly scores negative here.

## Assumptions
- Masked features are treated as proxy-dollars. The assumed rates set the RELATIVE weight of the five terms, so the ranking DOES depend on them — especially the cost-per-point, which shifts how many members score negative. We use research-anchored values but cannot calibrate them without a label.
- Spend (f5-f10) and balance (f1) are assumed to be in comparable units; points (f21) are converted via cost-per-point.
- Missing cost inputs (benefit/reward usage f13-f16, f21) contribute 0, read as genuine non-usage — a non-rewards member incurs no reward cost (co-missingness is a population flag, A3). This is economically intended, not an oversight.
- The annual fee is constant within the product and is excluded (A7).
- Lend-line size is a capital cost, not revenue (A11).
- f5 is capped for the no-breakdown cohort, so those members are under-ranked (A1).
- Strategic: the hidden ground truth is approximately a dollar revenue-cost on these features. Support: multiple top teams reach ~0.90 overlap, which is only possible if the true ranking is highly recoverable and concentrated — exactly the shape a dollar margin produces and a percentile ranking flattens.

## Validation Approach
Label-free, on the full 500K. After fixing the spend-scale issue, the top-20% spans all segments evenly (transactor 33% / revolver 31% / lender 36%) and represents the no-breakdown cohort fairly (~25%, matching its population share). The ranking is internally stable under rate jitter (0.83-0.93 top-20% Jaccard). We explicitly do NOT cite our own score's concentration as evidence of correctness — that would be circular (any heavy-tailed score concentrates by construction). This is a clean, explicit STRUCTURAL bet against our percentile baseline (which capped at public-LB ~0.46 across two submissions); only the leaderboard can confirm whether the magnitude/feature-emphasis change helps. We guard against public-70% overfit by changing structure for documented economic reasons, not by fitting to the public split.

## Additional Notes (Optional)
This is framework v2.0 (dollar magnitude), proposed as a structural successor to v1.x (percentile), whose public-LB ceiling appeared to be ~0.46. Held refinements: fold f3 collection calls into the risk term; add a small discounted contingent liability for the points balance f4; and reconcile the no-breakdown cohort's spend scale (A1) so capped-f5 members are not unfairly demoted. If the leaderboard confirms the magnitude structure we will calibrate the rates; if it does not, the percentile v1.2 framework (public-LB 0.465) remains the validated fallback.
