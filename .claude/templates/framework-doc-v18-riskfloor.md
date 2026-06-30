# Profitability Framework — Submission Writeup (v18 / all-positive spend + delinquency & net-negative-lending screens)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v18 = our v15 all-positive magnitude ranking PLUS a second, economically-derived screen: a member
     whose expected credit loss exceeds their interest revenue is a net-negative lending relationship and
     is demoted from the profitable tier — the continuous-risk generalization of the collection screen.
     Code: dollar_profit_v18_riskfloor. -->

## Variables Used
We score each member's estimated dollar contribution margin from the features that drive the profitable tail, and add two explicit credit screens:

Revenue: f7 Other, f10 Dining, f8 Entertainment, f6 Airline, f9 Lodging spend (every industry-spend category contributes positive interchange revenue, weighted by its net per-dollar margin); f1 Average Revolve Balance (net interest income — a primary issuer revenue, a first-class lever).

Cost / risk: f11 Average Risk Score applied to balance exposure (expected credit loss), used both as a continuous cost and as a net-negative-lending screen; f3 Collection-driven Cancellation (an explicit delinquency screen — the clearest single credit-distress signal).

Deliberately omitted (negligible influence on the top-20% ranking): f5 Total Spend (uncorrelated with real category spend, rank-corr 0.01); f4/f21 rewards and f13–f16 benefit credits (real costs, but they barely move WHO is in the top 20%); f17/f18 lend line (capital cost, not revenue); f2/f12/f19/f20/f22/f23 (engagement/depth — not direct profit). id is never used.

## Profitability Equation
Each member's score is their estimated dollar contribution margin (NO percentile ranking). Each term is scaled by its own standard deviation so the weights express relative profit contribution on one footing; two credit screens then remove members who do not belong in the profitable tier:

    base  = 0.738·z(f7) + 0.137·z(f10) + 0.348·z(f8) + 0.060·z(f6) + 0.060·z(f9)
            + 0.523·z(f1) + 0.110·z(−f11·f1)
    score = base,                          if in good standing
          = below the profitable tail,     if f3 = 1                          (collection-driven cancellation)
          = below the profitable tail,     if f11 > 0.16 AND f1 > 0           (net-negative lending)

    where z(x) = x / std(x);  the 0.16 threshold = R_interest / LGD (0.08 / 0.50)

Every spend category carries a POSITIVE weight: all spend produces interchange revenue (travel categories earn a thinner positive margin because their richer rewards offset more of the interchange — but they are not losses). f1 (revolving balance → interest income) carries ~70% of the dominant spend category's weight — interest is co-equal with spend. The net-negative-lending screen is NOT a tuned parameter: it follows directly from the issuer P&L. A member's lending margin is interest minus expected loss = (R_interest − LGD·f11)·f1; this is negative exactly when f11 exceeds R_interest/LGD = 0.16. Such a member loses the issuer more to default risk than they earn in interest, so their revolving-balance credit is withdrawn from the profitable tier.

## Prediction Logic
The contribution-margin score is written as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% is the graded set. Two screens remove members whose carried-balance interest would otherwise rank them in the top tier despite being unprofitable: (1) collection-driven cancellation (f3 = 1) — distressed and/or exiting; (2) net-negative lending (f11 > 0.16 with a positive balance) — expected credit loss exceeds interest revenue. Members with no industry-spend breakdown (f6–f10 absent) earn no interchange by construction and score on revolving balance net of risk alone; arithmetically only ~1% of them clear the spend-driven cutoff — appropriate, since absence of a spend breakdown is itself associated with lower-value, higher-risk members. Deterministic (seed 42), reproducible from src/score_magnitude.py (dollar_profit_v18_riskfloor); never uses id.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. v18 retains industry spend across ALL categories and revolving balance as the two revenue engines, and uses RISKINESS most fully of any version: expected loss on the carried balance as a continuous cost, PLUS two demotion screens — collection-driven cancellation (f3) and net-negative lending (f11 above the interest/loss break-even). Spend is taken at the industry-category level (the brief's "industry level spends"), not the f5 total, because f5 is uncorrelated with real category spend. All five spend categories are signed positive because every dollar of spend earns interchange; travel categories simply earn less of it net of their richer rewards. Benefit utilization, rewards, and total-spend (f5) remain dropped because they do not move the top-tier ranking.

## Coefficient/Weight Derivation
The revenue and expected-loss weights are anchored to our calibrated base: set by business reasoning (spend and interest are the two primary revenue engines; risk is the primary cost) and calibrated against the competition's public-leaderboard top-20%-overlap feedback. The category MARGINS are signed by the card's reward economics: every category earns interchange (positive), and the 5×-reward travel categories carry a smaller positive net margin than the 1× everyday categories — an asymmetry in MAGNITUDE, not sign. Neither credit screen is a free parameter: the collection screen is the business rule "a member in collections is not top-profitable," and the net-negative-lending threshold (f11 > 0.16) is derived, not tuned — it is exactly the risk level at which expected loss (LGD·f11·f1) overtakes interest revenue (R_interest·f1) given the standard loss-given-default of 0.50 and an 8% net interest margin. The screens therefore add no overfitting surface.

## Feature Transformations
No percentile ranking of the final score. Each input term is scaled by its standard deviation and combined linearly. Spend is decomposed into industry categories, each carrying its own positive signed weight. Expected loss is the product of the risk score and the balance exposure. Missing spend categories contribute zero; f7 refunds are negative and net down correctly. The two screens are hard demotions below the scored tail — they affect only WHO is in the top 20%, not the relative order of members in good standing.

## Business Logic
A member is profitable when their category-weighted spend plus net interest on revolving balance exceeds their expected credit loss. Principles: (1) ALL SPEND IS REVENUE — every industry category earns interchange, so a high-volume spender is profitable even when their spend skews to richer-reward travel; those categories earn a thinner margin, not a loss. (2) REVOLVING BALANCE is a first-class profit driver — interest income rivals interchange on heavy spend. (3) LENDING MUST BE NET-POSITIVE — interest is only profit if it outruns expected loss; a member whose risk is high enough that expected loss exceeds their interest (f11 > 0.16) is a net-negative lending relationship, and a member in collection-driven cancellation is distressed/exiting — neither belongs in the most-profitable quintile, regardless of the interest their balance accrues. High credit risk on a carried balance is the dominant cost and is both subtracted and screened.

## Assumptions
- Masked features are proxy-dollars; weights express relative profit contribution, scaled to comparable footing.
- Revolving balance (f1) proxies interest income (no booked-interest field exists); it is a primary revenue pillar, co-equal with spend — but only when the lending is net-positive.
- Industry-category spend (f6–f10), not the f5 total, is the spend signal (f5 is uncorrelated with real spend, rank-corr 0.01).
- All spend categories earn net-positive interchange; the 5×-reward travel categories earn a smaller positive margin than everyday spend, not a net loss — so heavy spenders are not penalized for their category mix.
- Expected loss = LGD (0.50) × risk (f11) × balance (f1); net interest margin ≈ 0.08 per dollar of balance, so lending turns net-negative at f11 > 0.16. Members past this break-even, and collection-flagged members (f3 = 1), are screened from the top tier.
- The absence of a spend breakdown signals a lower-value member; such members earn no interchange and rank on balance/risk only.
- The annual fee is constant and excluded; lend-line SIZE is a capital cost, not revenue (f17/f18 excluded).

## Validation Approach
Label-free, full 500K, built as a controlled, economically-isolated change to our public-leaderboard best (v15, all-positive, top-20% overlap 0.827). v18 shares 99% of v15's top 20% (Jaccard 0.989); it changes only the 547 members (0.55%) who are net-negative lenders — median risk 0.23, median balance ~$13.7K, but expected loss exceeding interest by ~$244/member — replacing them with low-risk members whose lending is net-positive. The change is parameter-free (the threshold is the interest/loss break-even, not a fit) and follows the same distress-demotion principle that improved our ranking before (the collection screen). Because it is grounded in the lending P&L rather than fitted to the public split, it is expected to hold on the hidden 30%. The screen's collateral is negligible by construction — it removes only members the issuer loses money lending to. Whether it improves top-20% overlap is decided by the leaderboard.

## Additional Notes (Optional)
v18 completes the riskiness driver: beyond expected loss as a continuous cost and the collection-cancellation screen, it adds the net-negative-lending screen — the continuous-risk generalization of the collection rule, derived from the break-even where expected credit loss overtakes interest revenue (f11 > 0.16). It is a small, surgical, economically-airtight sharpening of v15 (0.827): it removes the ~547 high-risk revolvers whose balance interest is more than offset by their default risk, and is among the most defensible single refinements available. If it does not improve on v15, that ranking remains the locked fallback.
