# Profitability Framework — Submission Writeup (v26 / multiplicative dual-engine: revolver spend compounds)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v26 = the hybrid-basis spend structure SCALED by (1 + revolving intensity): a revolver's spend is worth
     multiplicatively more because the issuer earns interchange on the spend AND interest on the balance from
     one compounding relationship. Transactors (no balance) are scored on spend alone. Code: dollar_profit_v26_multiengine. -->

## Variables Used
We score each member's estimated dollar contribution margin, with the spend value scaled up for members who also revolve, plus a credit-distress screen:

Revenue: f7 Other Spend (dominant general-spend category, dollar basis) and f8 Entertainment, f10 Dining, f6 Airline, f9 Lodging spend (specialty categories, rank basis) — together the spend component; f1 Average Revolve Balance (net interest income, entering BOTH as the multiplier on spend AND as an additive co-equal term).

Cost / risk: f11 Average Risk Score applied to balance exposure (expected credit loss); f3 Collection-driven Cancellation (delinquency screen).

Deliberately omitted (negligible influence on the top-20% ranking): f5 Total Spend (uncorrelated with real category spend, rank-corr 0.01); f4/f21 rewards and f13–f16 benefit credits (real costs, but they barely move WHO is in the top 20%); f17/f18 lend line (capital cost, not revenue); f2/f12/f19/f20/f22/f23 (engagement/depth — not direct profit). id is never used.

## Profitability Equation
Each member's score is their estimated dollar contribution margin (NO percentile ranking of the final score). The spend component (general spend in dollars, specialty categories by rank) is SCALED by a revolving-intensity multiplier, so a dollar of spend from a revolver is worth more than the same dollar from a transactor; revolving balance also enters additively; expected loss is subtracted; and members in collections are screened out:

    spend  = 0.738·z(f7) + 0.348·r(f8) + 0.137·r(f10) + 0.060·r(f6) + 0.060·r(f9)   [general in $, specialty by rank]
    base   = spend · ( 1 + 0.9·revolving_intensity )          [MULTIPLICATIVE: revolver spend compounds]
             + 0.738·z(f1)                                     [additive net interest, co-equal]
             + 0.110·z(−f11·f1)                                [expected credit loss]
             where revolving_intensity = rank(f1) for revolvers, 0 for transactors (f1 = 0)
    score  = base,                          if f3 = 0
           = below the profitable tail,     if f3 = 1  (collection-driven cancellation → delinquency screen)

    where z(x) = x / std(x)   and   r(x) = percentile-rank(x) / std(percentile-rank(x))

The multiplier is the core idea: for a pure transactor (revolving balance = 0) the factor is exactly 1, so their spend is counted at face value; for a revolver it rises up to ~1.9×, reflecting that the issuer earns interchange on their spend AND interest on their balance from one relationship — the two revenue streams compound rather than simply add. The collection screen is a business rule, not a tuned weight.

## Prediction Logic
The contribution-margin score is written as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% is the graded set. Members flagged for collection-driven cancellation (f3 = 1) are screened out. Because the multiplier is exactly 1 for transactors, the highest-spend pure-transactor members are scored on spend alone and overwhelmingly retained (in-rate ~0.99). The multiplicative form promotes high-spend members who also carry a balance — the dual-engine relationships — lifting the profitable tier toward members who generate both revenue streams. Members with no industry-spend breakdown score on balance net of risk alone; combined with the screen they remain ~1% of the top 20%. Deterministic (seed 42), reproducible from src/score_magnitude.py (dollar_profit_v26_multiengine); never uses id.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. v26 models spend behavior and revolving patterns as INTERACTING rather than independent: a member who both spends and revolves is worth more than the sum, because the two revenue streams come from one relationship. Spend is taken at the industry-category level (the brief's "industry level spends"), not the f5 total; the dominant general category is measured in dollars and the specialty categories by rank. Riskiness enters as expected loss plus the collection screen. Benefit utilization, rewards, and total-spend (f5) remain dropped because they do not move the top-tier ranking.

## Coefficient/Weight Derivation
The spend-component and additive weights are unchanged from the calibrated v19/v22 framework (net-interest-grounded f1 co-equal; general spend in dollars; specialty categories on a rank basis; expected-loss term). The one new parameter is the multiplier strength (0.9): it is set at the level that makes a substantial dual-engine reweighting while still retaining ~99% of the highest-conviction pure-spend members in the top tier — beyond it the multiplier begins displacing those members, which prior testing (blanket lending up-weighting) showed does not help. The multiplicative form itself follows from the economics: interchange and interest from the same member are one compounding relationship, not two independent lines.

## Feature Transformations
No percentile ranking of the final score. General spend (f7) and revolving balance (f1) are scaled by standard deviation; specialty categories (f8, f10, f6, f9) are transformed to within-category percentile rank. The spend component is then multiplied by (1 + 0.9 × revolving-intensity), where revolving-intensity is the percentile rank of the balance for revolvers and zero for transactors. Revolving balance also enters additively, and expected loss is the product of the risk score and balance exposure. Missing spend contributes at the low end; f7 refunds net down. The delinquency screen is a hard demotion of f3 = 1 members below the scored tail.

## Business Logic
A member is profitable when their spend interchange plus net interest exceeds their expected credit loss — and for a member who does both, the two revenue streams compound within one relationship. Principles: (1) REVOLVER SPEND COMPOUNDS — a dollar of spend from a member who also carries a balance is worth more than the same dollar from a transactor, because the issuer earns interchange on the spend and interest on the balance from one engaged, higher-retention relationship; this is modelled multiplicatively. (2) LENDING IS A FIRST-CLASS PROFIT ENGINE — net interest (~12% yield) also enters additively, co-equal with spend. (3) DOLLARS WHERE BOOKED, RANK WHERE MAGNITUDE MISLEADS — general spend and interest are measured in dollars; the smaller specialty categories by rank so one outsized specialty purchase does not masquerade as broad profitability. (4) a member flagged for COLLECTION-DRIVEN CANCELLATION is distressed/exiting and is screened out. High credit risk on a carried balance is the dominant cost and is subtracted.

## Assumptions
- Masked features are proxy-dollars; weights express relative profit contribution, scaled to comparable footing.
- Revolving balance (f1) proxies interest income (no booked-interest field); at ~12% net interest yield it is a primary revenue pillar, entering both as the spend multiplier and additively co-equal with spend.
- A revolver's spend and balance are one compounding relationship (interchange + interest), so revolver spend is worth multiplicatively more than transactor spend; transactors (no balance) are scored on spend at face value.
- General spend (f7) and balance (f1) are booked revenue linear in dollars → measured in dollars; specialty categories (f6/f8/f9/f10) are skewed lines → measured by within-category rank.
- Industry-category spend (f6–f10), not the f5 total, is the spend signal (f5 uncorrelated with real spend, rank-corr 0.01).
- f3 = 1 (collection-driven cancellation) marks a distressed/exiting member excluded from the top tier; removed members are overwhelmingly low-spend.
- The absence of a spend breakdown signals a lower-value member; such members rank on balance/risk only and are not over-promoted.
- The annual fee is constant and excluded; lend-line SIZE is a capital cost, not revenue (f17/f18 excluded).

## Validation Approach
Label-free, full 500K, built as a structural extension of the current public-leaderboard best (v24 additive dual-engine, top-20% overlap 0.880), which established that rewarding dual-engine members gains. v26 tests the stronger claim that the two revenue streams compound (multiplicative) rather than add. The highest-conviction members are largely preserved: because the multiplier is exactly 1 for transactors, the pure-transactor high-spend "whales" retain a ~0.990 in-rate. The multiplicative form reshuffles ~9,300 members at the boundary (Jaccard 0.83 versus v24), lifting the top tier to ~74% revolver — a substantial bet that the true top-20% is markedly dual-engine-heavy, consistent with the direction of every confirmed gain (revolving up-weight, dual-engine premium) but a bigger step. It is a deliberate higher-variance submission: the multiplier strength is capped to retain ~99% of the whales, and the form is grounded in relationship economics rather than fitted to the public split, but only the leaderboard can confirm how dual-engine-heavy the truth is. The score is non-degenerate (402,512 distinct values) with no collection-flagged members in the top tier; the prior best (0.880) is retained regardless, as the leaderboard counts the best submission.

## Additional Notes (Optional)
v26 escalates the dual-engine idea from an additive bonus (v24, which won) to a multiplicative form: a revolver's spend is worth up to ~1.9× a transactor's, because the interchange and interest come from one compounding relationship. It keeps the validated spine — general spend in dollars, specialty categories by rank, additive co-equal lending, expected loss, and the collection-driven-cancellation screen — and caps the multiplier to retain the high-conviction members. This is the framework's boldest single bet on the hypothesis that the issuer's most profitable cardmembers are overwhelmingly those who both spend and borrow. The full development path is documented in the project report.
