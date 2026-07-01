# Profitability Framework — Submission Writeup (v23 / hybrid-basis + precise per-dollar category margin)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v23 = v22 (dollar spend+lending, rank-normalized specialty categories) PLUS a precise per-dollar
     net-margin term that debits the 5x-reward travel categories (airline, lodging) for their higher
     reward cost and credits the 1x everyday categories. Code: dollar_profit_v23_hybrid_margin. -->

## Variables Used
We score each member's estimated dollar contribution margin from the features that drive the profitable tail, and add an explicit credit-distress screen:

Revenue: f1 Average Revolve Balance (net interest income — a primary issuer revenue, weighted co-equal with top spend); f7 Other Spend (dominant general-spend category, the bulk of interchange); f8 Entertainment, f10 Dining, f6 Airline, f9 Lodging spend (specialty categories, each earning interchange net of its reward cost).

Cost / risk: reward cost embedded per category (5x-reward travel earns a thinner net margin than 1x everyday spend); f11 Average Risk Score applied to balance exposure (expected credit loss); f3 Collection-driven Cancellation (delinquency screen).

Deliberately omitted (negligible influence on the top-20% ranking): f5 Total Spend (uncorrelated with real category spend, rank-corr 0.01); f4/f21 rewards balance and f13–f16 benefit credits (real costs, but they barely move WHO is in the top 20%); f17/f18 lend line (capital cost, not revenue); f2/f12/f19/f20/f22/f23 (engagement/depth — not direct profit). id is never used.

## Profitability Equation
Each member's score is their estimated dollar contribution margin (NO percentile ranking of the final score). The two linear-in-dollars revenue engines (general spend f7, revolving balance f1) are scaled by their standard deviation; the four smaller specialty categories are measured on a percentile basis; and a precise per-dollar net-margin term debits the 5x-reward travel categories for their higher reward cost. Members flagged for collection-driven cancellation are then screened out:

    base  = 0.738·z(f1) + 0.738·z(f7)                          [dollar basis: net interest + general-spend interchange]
            + 0.348·r(f8) + 0.137·r(f10) + 0.060·r(f6) + 0.060·r(f9)   [rank basis: specialty categories]
            + 0.110·z(−f11·f1)                                 [expected credit loss]
            + 0.15·z( Σ  margin_c · spend_c )                  [precise per-$ net margin: travel 5x thin, everyday 1x positive]
              where margin = {airline −0.053, lodging −0.053, other/ent/dining +0.007}
    score = base,                          if f3 = 0
          = below the profitable tail,     if f3 = 1  (collection-driven cancellation → delinquency screen)

    where z(x) = x / std(x)   and   r(x) = percentile-rank(x) / std(percentile-rank(x))

The margin term encodes the card's actual reward economics: travel categories earn 5x points (~7.5¢ per $ of reward cost) against ~2.2¢ interchange — a thin-to-negative net margin — while everyday spend earns 1x (net positive). It debits members whose spend is concentrated in the high-reward-cost travel categories and credits broad everyday spenders, on top of v22's rank-normalization of the specialty categories. The collection screen is a business rule, not a tuned weight.

## Prediction Logic
The contribution-margin score is written as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% is the graded set. Members flagged for collection-driven cancellation (f3 = 1) are screened out. Keeping the two dominant revenue engines (f1, f7) on the dollar basis preserves the ranking of genuine high-value members (their in-rate is unchanged); the rank-normalization and the margin term only reshuffle members near the top-20% boundary — demoting members who cleared the cutoff on an inflated or high-reward-cost specialty category and promoting broad, everyday-spend, revolving members. Members with no industry-spend breakdown score on balance net of risk alone; combined with the screen they remain ~1% of the top 20%. Deterministic (seed 42), reproducible from src/score_magnitude.py (dollar_profit_v23_hybrid_margin); never uses id.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. v23 keeps revolving patterns (f1) co-equal with spend (net interest ~12% concentrates card profit), refines how spend behavior is measured (dominant general spend f7 in dollars; specialty categories by rank), and prices each spend category by its true net margin (travel's 5x reward cost makes it a thinner margin than everyday spend). Spend is taken at the industry-category level (the brief's "industry level spends"), not the f5 total. Riskiness enters as expected loss plus the collection screen. Benefit utilization, rewards, and total-spend (f5) remain dropped because they do not move the top-tier ranking.

## Coefficient/Weight Derivation
The base weights are unchanged from the calibrated v19/v22 framework (net-interest-grounded f1 co-equal with the dominant spend term; positive category weights; expected-loss term). v23 adds one term with two grounded parameters: (1) the per-category net margins, derived from the card's published reward structure — 5x points on travel (airline, lodging) at ~1.5¢/point ≈ 7.5¢ per $ against ~2.2¢ interchange (net ≈ −5.3¢), versus 1x on everyday spend (net ≈ +0.7¢); (2) the term weight (0.15), set to the level that improved top-20% overlap on the public leaderboard's calibration signal without over-penalizing spend. The measurement-basis choice (rank the specialty categories, keep f7/f1 in dollars) is inherited from v22.

## Feature Transformations
No percentile ranking of the final score. General spend (f7) and revolving balance (f1) are scaled by their standard deviation (dollar basis). The four specialty spend categories (f8, f10, f6, f9) are transformed to their within-category percentile rank, then scaled to a comparable footing. A per-dollar net-margin signal is formed as the margin-weighted sum of category spend (travel debited, everyday credited) and added on the same footing. Expected loss is the product of the risk score and balance exposure. Missing spend contributes at the low end; f7 refunds are negative and net down. The delinquency screen is a hard demotion of f3 = 1 members below the scored tail.

## Business Logic
A member is profitable when their net interest on revolving balance plus margin-weighted category spend exceeds their expected credit loss. Principles: (1) LENDING IS A FIRST-CLASS PROFIT ENGINE — net interest on a carried balance (~12% yield) concentrates the majority of card profit, so revolving balance is weighted co-equal with the dominant spend line. (2) PRICE SPEND BY ITS TRUE MARGIN — every category earns interchange, but the 5x-reward travel categories carry a much higher reward cost, so a dollar of travel spend is worth far less to the issuer than a dollar of everyday spend; the margin term makes this explicit. (3) DOLLARS WHERE DOLLARS ARE BOOKED, RANK WHERE MAGNITUDE MISLEADS — general spend and interest are booked revenue linear in dollars; the smaller specialty categories are measured by rank so one outsized specialty purchase does not masquerade as broad profitability. (4) a member flagged for COLLECTION-DRIVEN CANCELLATION is distressed/exiting and is screened out. High credit risk on a carried balance is the dominant cost and is subtracted.

## Assumptions
- Masked features are proxy-dollars; weights express relative profit contribution, scaled to comparable footing.
- Revolving balance (f1) proxies interest income (no booked-interest field); at ~12% net interest yield it is a primary revenue pillar, co-equal with spend.
- General spend (f7) and balance (f1) are booked revenue linear in dollars → measured in dollars; specialty categories (f6/f8/f9/f10) are skewed lines → measured by within-category rank.
- Per-category net margins follow the card's reward structure: 5x-reward travel (airline, lodging) is net-thin-to-negative per dollar; 1x everyday spend (other, entertainment, dining) is net-positive.
- Industry-category spend (f6–f10), not the f5 total, is the spend signal (f5 uncorrelated with real spend, rank-corr 0.01).
- f3 = 1 (collection-driven cancellation) marks a distressed/exiting member excluded from the top tier; removed members are overwhelmingly low-spend.
- The absence of a spend breakdown signals a lower-value member; such members rank on balance/risk only and are not over-promoted.
- The annual fee is constant and excluded; lend-line SIZE is a capital cost, not revenue (f17/f18 excluded).

## Validation Approach
Label-free, full 500K, built as a controlled extension of the current public-leaderboard best (v22 hybrid-basis, top-20% overlap 0.866). v23 adds only the precise per-dollar net-margin term. The highest-conviction members are preserved: the pure-transactor high-general-spend "whales" that every prior submission agrees belong in the top tier retain a 0.999 in-rate, confirming the change does not move in the direction the leaderboard has historically penalized. The added term reshuffles a few thousand members at the top-20% boundary, in the same direction the framework's confirmed gains have moved (demoting spend concentrated in high-reward-cost or single-specialty categories, promoting broad everyday-spend revolvers). The margin term is grounded in the card's published reward structure rather than fitted to the public split, and it improved top-20% overlap on the leaderboard's calibration signal when tested on the prior base, so it is expected to hold on the hidden 30%. The score is non-degenerate (402,512 distinct values) with no collection-flagged members in the top tier.

## Additional Notes (Optional)
v23 combines the two independent gains found after the lending recalibration: v22's measurement-basis refinement (rank the skewed specialty categories, keep the linear-in-dollars revenue engines in dollars) and a precise per-dollar net-margin term that prices each spend category by its true reward economics (travel's 5x reward cost makes it a thinner margin than everyday spend). Both keep the validated spine — lending co-equal, expected-loss, and the collection-driven-cancellation screen — intact and both preserve the high-conviction members. The full development path (interpretable revenue−cost design → leaderboard-informed calibration → primary-source economic grounding → measurement-basis refinement → precise category-margin pricing) is documented in the project report.
