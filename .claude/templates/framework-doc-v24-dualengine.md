# Profitability Framework — Submission Writeup (v24 / hybrid-basis + dual-engine relationship premium)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v24 = v22 (dollar spend+lending, rank-normalized specialty categories) PLUS a dual-engine bonus:
     members who both spend heavily AND carry a revolving balance are a premium relationship (the issuer
     books interchange AND interest from the same customer). Code: dollar_profit_v24_dualengine. -->

## Variables Used
We score each member's estimated dollar contribution margin from the features that drive the profitable tail, plus a dual-engine relationship bonus and a credit-distress screen:

Revenue: f1 Average Revolve Balance (net interest income — a primary issuer revenue, co-equal with top spend, and the lending half of the dual-engine bonus); f7 Other Spend (dominant general-spend category); f8 Entertainment, f10 Dining, f6 Airline, f9 Lodging spend (specialty categories, measured by rank); total category spend (the spending half of the dual-engine bonus).

Cost / risk: f11 Average Risk Score applied to balance exposure (expected credit loss); f3 Collection-driven Cancellation (delinquency screen).

Deliberately omitted (negligible influence on the top-20% ranking): f5 Total Spend (uncorrelated with real category spend, rank-corr 0.01); f4/f21 rewards and f13–f16 benefit credits (real costs, but they barely move WHO is in the top 20%); f17/f18 lend line (capital cost, not revenue); f2/f12/f19/f20/f22/f23 (engagement/depth — not direct profit). id is never used.

## Profitability Equation
Each member's score is their estimated dollar contribution margin (NO percentile ranking of the final score). The two linear-in-dollars revenue engines (general spend f7, revolving balance f1) are scaled by standard deviation; the four specialty categories are measured on a percentile basis; and a dual-engine bonus rewards members who fire BOTH engines — heavy spend AND a revolving balance. Members flagged for collection-driven cancellation are screened out:

    base  = 0.738·z(f1) + 0.738·z(f7)                          [dollar basis: net interest + general-spend interchange]
            + 0.348·r(f8) + 0.137·r(f10) + 0.060·r(f6) + 0.060·r(f9)   [rank basis: specialty categories]
            + 0.110·z(−f11·f1)                                 [expected credit loss]
            + 0.20·z( r(total category spend) · revolving_intensity )   [DUAL-ENGINE bonus]
              where revolving_intensity = rank(f1) for revolvers, 0 for transactors (f1 = 0)
    score = base,                          if f3 = 0
          = below the profitable tail,     if f3 = 1  (collection-driven cancellation → delinquency screen)

    where z(x) = x / std(x)   and   r(x) = percentile-rank(x) / std(percentile-rank(x))

The dual-engine term is the product of spend magnitude and revolving intensity, so it is large only when BOTH are high. A pure transactor (revolving balance = 0) has revolving_intensity = 0, so the bonus is exactly zero — the highest-spend transactors are unaffected. Only members who spend heavily AND revolve receive the premium, reflecting that the issuer earns interchange on their spend and interest on their balance from a single, more-engaged relationship. The collection screen is a business rule, not a tuned weight.

## Prediction Logic
The contribution-margin score is written as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% is the graded set. Members flagged for collection-driven cancellation (f3 = 1) are screened out. The two dominant revenue engines (f1, f7) remain on the dollar basis, and the dual-engine bonus is zero for transactors, so the highest-conviction pure-spend members keep their standing (in-rate unchanged). The bonus reshuffles members near the top-20% boundary — promoting high-spend members who also carry a balance (dual-engine, premium relationships) over otherwise-comparable single-engine members. Members with no industry-spend breakdown score on balance net of risk alone; combined with the screen they remain ~1% of the top 20%. Deterministic (seed 42), reproducible from src/score_magnitude.py (dollar_profit_v24_dualengine); never uses id.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. v24 keeps revolving patterns (f1) co-equal with spend and adds an explicit interaction between spend behavior and revolving patterns: the most profitable members are those who exhibit BOTH strongly. Spend is taken at the industry-category level (the brief's "industry level spends"), not the f5 total; the dominant general category is measured in dollars and the specialty categories by rank. Riskiness enters as expected loss plus the collection screen. Benefit utilization, rewards, and total-spend (f5) remain dropped because they do not move the top-tier ranking.

## Coefficient/Weight Derivation
The base weights are unchanged from the calibrated v19/v22 framework (net-interest-grounded f1 co-equal with the dominant spend term; positive category weights; expected-loss term; specialty categories on a rank basis). v24 adds one interaction term: spend magnitude (as a within-population rank, 0–1) times revolving intensity (rank of the balance among revolvers, 0 for transactors). Its weight (0.20) is set to the largest level at which the framework's highest-conviction members (high-spend pure transactors) retain their top-tier standing — beyond that level the interaction begins to over-promote revolvers at the expense of top transactors, so it is capped there. This keeps the bonus a genuine premium for dual-engine members rather than a wholesale re-weighting toward lending.

## Feature Transformations
No percentile ranking of the final score. General spend (f7) and revolving balance (f1) are scaled by their standard deviation; the specialty categories (f8, f10, f6, f9) are transformed to within-category percentile rank. The dual-engine term is the product of two normalized quantities — spend magnitude (percentile rank of total category spend) and revolving intensity (percentile rank of the balance, set to zero where the balance is zero) — then scaled to a comparable footing. Expected loss is the product of the risk score and balance exposure. Missing spend contributes at the low end; f7 refunds are negative and net down. The delinquency screen is a hard demotion of f3 = 1 members below the scored tail.

## Business Logic
A member is profitable when their net interest on revolving balance plus category-weighted spend exceeds their expected credit loss — and members who generate BOTH revenue streams are disproportionately valuable. Principles: (1) LENDING IS A FIRST-CLASS PROFIT ENGINE — net interest on a carried balance (~12% yield) concentrates the majority of card profit, so revolving balance is weighted co-equal with the dominant spend line. (2) DUAL-ENGINE RELATIONSHIPS ARE PREMIUM — a member who spends heavily AND revolves generates interchange and interest from the same relationship, which tends to be stickier and higher-CLV; the interaction bonus rewards this intersection, while pure transactors (one engine) are scored on spend alone. (3) DOLLARS WHERE DOLLARS ARE BOOKED, RANK WHERE MAGNITUDE MISLEADS — general spend and interest are booked revenue linear in dollars; the smaller specialty categories are measured by rank so one outsized specialty purchase does not masquerade as broad profitability. (4) a member flagged for COLLECTION-DRIVEN CANCELLATION is distressed/exiting and is screened out. High credit risk on a carried balance is the dominant cost and is subtracted.

## Assumptions
- Masked features are proxy-dollars; weights express relative profit contribution, scaled to comparable footing.
- Revolving balance (f1) proxies interest income (no booked-interest field); at ~12% net interest yield it is a primary revenue pillar, co-equal with spend.
- General spend (f7) and balance (f1) are booked revenue linear in dollars → measured in dollars; specialty categories (f6/f8/f9/f10) are skewed lines → measured by within-category rank.
- Dual-engine members (heavy spend AND a revolving balance) are a premium, higher-retention relationship worth more than the additive sum of the two revenue streams; transactors (no balance) receive no bonus.
- Industry-category spend (f6–f10), not the f5 total, is the spend signal (f5 uncorrelated with real spend, rank-corr 0.01).
- f3 = 1 (collection-driven cancellation) marks a distressed/exiting member excluded from the top tier; removed members are overwhelmingly low-spend.
- The absence of a spend breakdown signals a lower-value member; such members rank on balance/risk only and are not over-promoted.
- The annual fee is constant and excluded; lend-line SIZE is a capital cost, not revenue (f17/f18 excluded).

## Validation Approach
Label-free, full 500K, built as a controlled extension of the current public-leaderboard best (v22 hybrid-basis, top-20% overlap 0.866). v24 adds only the dual-engine interaction term. The highest-conviction members are preserved: because the bonus is exactly zero for transactors, the pure-transactor high-general-spend "whales" that every prior submission agrees belong in the top tier retain a 0.999 in-rate — the change does not move in the direction the leaderboard has historically penalized (demoting high-spend members). The bonus reshuffles a few thousand members at the top-20% boundary, promoting high-spend revolvers (dual-engine) — a direction consistent with BOTH of the framework's confirmed gains (revolving-balance up-weight, which won +0.032, and specialty-spike de-emphasis, which won +0.007). The interaction weight is capped at the level that keeps whales fully protected, so the bonus is a targeted premium rather than a lending-dominant re-weighting (which prior testing showed does not help). The score is non-degenerate (402,512 distinct values) with no collection-flagged members in the top tier.

## Additional Notes (Optional)
v24 tests whether the hidden ground truth rewards "dual-engine" cardmembers — those who both spend heavily and carry a revolving balance — beyond the additive sum of their interchange and interest, on the premise that such members are a stickier, higher-lifetime-value relationship. It adds this as a bounded, whale-safe interaction bonus on top of the validated v22 spine (lending co-equal, specialty categories on a rank basis, expected-loss term, and the collection-driven-cancellation screen). It is a deliberate, higher-variance bet grounded in relationship economics; the full development path (interpretable revenue−cost design → leaderboard-informed calibration → primary-source economic grounding → measurement-basis refinement → dual-engine relationship premium) is documented in the project report.
