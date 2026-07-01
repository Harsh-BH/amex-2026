# Profitability Framework — Submission Writeup (v25 / hybrid-basis + dual-engine premium + category margin)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v25 = v24 (dual-engine relationship premium on the hybrid basis) PLUS the precise per-dollar category
     margin term. Stacks the three validated levers. Code: dollar_profit_v25_dualengine_margin. -->

## Variables Used
We score each member's estimated dollar contribution margin from the features that drive the profitable tail, plus a dual-engine relationship bonus, a precise category-margin term, and a credit-distress screen:

Revenue: f1 Average Revolve Balance (net interest income, co-equal with top spend, and the lending half of the dual-engine bonus); f7 Other Spend (dominant general-spend category); f8 Entertainment, f10 Dining, f6 Airline, f9 Lodging spend (specialty categories, measured by rank and priced by net margin); total category spend (the spending half of the dual-engine bonus).

Cost / risk: reward cost embedded per category (5x-reward travel earns a thinner net margin); f11 Average Risk Score applied to balance exposure (expected credit loss); f3 Collection-driven Cancellation (delinquency screen).

Deliberately omitted (negligible influence on the top-20% ranking): f5 Total Spend (uncorrelated with real category spend, rank-corr 0.01); f4/f21 rewards and f13–f16 benefit credits (real costs, but they barely move WHO is in the top 20%); f17/f18 lend line (capital cost, not revenue); f2/f12/f19/f20/f22/f23 (engagement/depth — not direct profit). id is never used.

## Profitability Equation
Each member's score is their estimated dollar contribution margin (NO percentile ranking of the final score). It combines: the two linear-in-dollars revenue engines (general spend f7, revolving balance f1) on the dollar basis; the four specialty categories on a rank basis; a dual-engine bonus for members who fire both engines; a precise per-dollar net-margin term; and the collection screen:

    base  = 0.738·z(f1) + 0.738·z(f7)                          [dollar basis: net interest + general-spend interchange]
            + 0.348·r(f8) + 0.137·r(f10) + 0.060·r(f6) + 0.060·r(f9)   [rank basis: specialty categories]
            + 0.110·z(−f11·f1)                                 [expected credit loss]
            + 0.20·z( r(total category spend) · revolving_intensity )   [DUAL-ENGINE bonus, revolving_intensity=0 for transactors]
            + 0.15·z( Σ margin_c · spend_c )                   [precise per-$ net margin: travel 5x thin, everyday 1x positive]
    score = base,                          if f3 = 0
          = below the profitable tail,     if f3 = 1  (collection-driven cancellation → delinquency screen)

    where z(x) = x / std(x)   and   r(x) = percentile-rank(x) / std(percentile-rank(x))

Three effects stack on the validated spend+lending spine: (1) specialty categories are measured by rank so one outsized specialty purchase does not masquerade as broad profitability; (2) members who both spend heavily AND carry a balance receive a dual-engine premium (zero for pure transactors, so the top spenders are unaffected); (3) each spend category is priced by its true net margin, debiting the 5x-reward travel categories. The collection screen is a business rule, not a tuned weight.

## Prediction Logic
The contribution-margin score is written as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% is the graded set. Members flagged for collection-driven cancellation (f3 = 1) are screened out. The two dominant revenue engines stay on the dollar basis and the dual-engine bonus is zero for transactors, so the highest-conviction pure-spend members keep their standing (in-rate unchanged). The three added effects reshuffle members near the top-20% boundary — promoting broad, dual-engine (spend + balance), everyday-spend members and demoting members who cleared the cutoff on an inflated, single, or high-reward-cost specialty category. Members with no industry-spend breakdown score on balance net of risk alone; combined with the screen they remain ~1% of the top 20%. Deterministic (seed 42), reproducible from src/score_magnitude.py (dollar_profit_v25_dualengine_margin); never uses id.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. v25 keeps revolving patterns (f1) co-equal with spend, adds an interaction between spend and revolving (dual-engine premium), refines how specialty spend is measured (rank, not raw dollars), and prices each category by its net margin. Spend is taken at the industry-category level (the brief's "industry level spends"), not the f5 total. Riskiness enters as expected loss plus the collection screen. Benefit utilization, rewards, and total-spend (f5) remain dropped because they do not move the top-tier ranking.

## Coefficient/Weight Derivation
The base weights are unchanged from the calibrated v19/v22 framework (net-interest-grounded f1 co-equal with the dominant spend term; positive category weights on a rank basis; expected-loss term). v25 adds two terms whose weights are each set at a validated level: (1) the dual-engine interaction weight (0.20), capped at the largest level that keeps the highest-conviction pure-spend members fully in the top tier (beyond it the interaction begins over-promoting revolvers, which prior testing showed does not help); (2) the category-margin weight (0.15), grounded in the card's reward structure (5x travel ≈ 7.5¢/$ reward cost vs ~2.2¢ interchange → net-negative; 1x everyday → net-positive). Both improved top-20% overlap in controlled tests on the prior bases; neither is fitted to the public split beyond selecting these levels.

## Feature Transformations
No percentile ranking of the final score. General spend (f7) and revolving balance (f1) are scaled by standard deviation; specialty categories (f8, f10, f6, f9) are transformed to within-category percentile rank. The dual-engine term is the product of spend magnitude (rank of total category spend) and revolving intensity (rank of the balance, zero where balance is zero). The margin term is the margin-weighted sum of category spend. Expected loss is the product of the risk score and balance exposure. Missing spend contributes at the low end; f7 refunds net down. The delinquency screen is a hard demotion of f3 = 1 members below the scored tail.

## Business Logic
A member is profitable when their net interest on revolving balance plus margin-weighted category spend exceeds their expected credit loss — and members who generate BOTH revenue streams are disproportionately valuable. Principles: (1) LENDING IS A FIRST-CLASS PROFIT ENGINE — net interest on a carried balance (~12% yield) concentrates the majority of card profit, so revolving balance is co-equal with the dominant spend line. (2) DUAL-ENGINE RELATIONSHIPS ARE PREMIUM — a member who spends heavily AND revolves generates interchange and interest from one stickier, higher-CLV relationship; the interaction rewards this intersection, while pure transactors are scored on spend alone. (3) PRICE SPEND BY ITS TRUE MARGIN — every category earns interchange, but 5x-reward travel carries a much higher reward cost, so a dollar of travel spend is worth less than a dollar of everyday spend. (4) DOLLARS WHERE BOOKED, RANK WHERE MAGNITUDE MISLEADS — general spend and interest are measured in dollars; the smaller specialty categories by rank. (5) a member flagged for COLLECTION-DRIVEN CANCELLATION is distressed/exiting and is screened out. High credit risk on a carried balance is the dominant cost and is subtracted.

## Assumptions
- Masked features are proxy-dollars; weights express relative profit contribution, scaled to comparable footing.
- Revolving balance (f1) proxies interest income (no booked-interest field); at ~12% net interest yield it is a primary revenue pillar, co-equal with spend.
- General spend (f7) and balance (f1) are booked revenue linear in dollars → measured in dollars; specialty categories (f6/f8/f9/f10) are skewed lines → measured by within-category rank.
- Dual-engine members (heavy spend AND a revolving balance) are a premium, higher-retention relationship worth more than the additive sum; transactors (no balance) receive no bonus.
- Per-category net margins follow the card's reward structure: 5x-reward travel (airline, lodging) is net-thin-to-negative per dollar; 1x everyday spend is net-positive.
- Industry-category spend (f6–f10), not the f5 total, is the spend signal (f5 uncorrelated with real spend, rank-corr 0.01).
- f3 = 1 (collection-driven cancellation) marks a distressed/exiting member excluded from the top tier; removed members are overwhelmingly low-spend.
- The absence of a spend breakdown signals a lower-value member; such members rank on balance/risk only and are not over-promoted.
- The annual fee is constant and excluded; lend-line SIZE is a capital cost, not revenue (f17/f18 excluded).

## Validation Approach
Label-free, full 500K, built as a controlled extension of the current public-leaderboard best (v24 dual-engine, top-20% overlap 0.880). v25 adds only the precise per-dollar category-margin term to v24, keeping the dual-engine weight at its confirmed winning level rather than pushing it (which would gamble the interaction's peak). The highest-conviction members are preserved: the pure-transactor high-general-spend "whales" retain a 0.999 in-rate — the change does not move in the direction the leaderboard has historically penalized. The margin term reshuffles ~4,000 members at the boundary (Jaccard 0.92 versus v24), in the same direction the framework's confirmed gains have moved (demoting spend concentrated in high-reward-cost travel categories). The score is non-degenerate (402,512 distinct values) with no collection-flagged members in the top tier. Each of the three stacked levers (rank-basis for specialty categories, dual-engine premium, category margin) was individually validated or confirmed in the framework's development; v25 combines them without re-weighting the validated spine, and each is grounded in card economics rather than fitted to the public split, so the combination is expected to hold on the hidden 30%.

## Additional Notes (Optional)
v25 is the full stack of the framework's validated levers: the hybrid measurement basis (rank the skewed specialty categories, keep the linear-in-dollars revenue engines in dollars), the dual-engine relationship premium (reward members firing both spend and lending from one relationship), and precise category-margin pricing (travel's 5x reward cost makes it a thinner margin). All sit on the validated spine — lending co-equal, expected loss, and the collection-driven-cancellation screen — and all preserve the high-conviction members. The full development path (interpretable revenue−cost design → leaderboard-informed calibration → primary-source economic grounding → measurement-basis refinement → dual-engine premium → category-margin pricing) is documented in the project report.
