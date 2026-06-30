# Profitability Framework — Submission Writeup (v15 / all-positive spend + delinquency screen)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v15 = our calibrated v10/v11 magnitude ranking with ALL spend categories treated as net-POSITIVE
     interchange revenue (airline & lodging earn less per dollar than everyday spend, but are not
     penalized), the lodging category restored, plus the validated collection-delinquency screen.
     Code: dollar_profit_v15_allpos. -->

## Variables Used
We score each member's estimated dollar contribution margin from the features that drive the profitable tail, and add an explicit credit-distress screen:

Revenue: f7 Other, f10 Dining, f8 Entertainment, f6 Airline, f9 Lodging spend (every industry-spend category contributes positive interchange revenue, weighted by its net per-dollar margin); f1 Average Revolve Balance (net interest income — a primary issuer revenue, a first-class lever).

Cost / risk: f11 Average Risk Score applied to balance exposure (expected credit loss); f3 Collection-driven Cancellation (an explicit delinquency screen — the clearest single credit-distress signal).

Deliberately omitted (negligible influence on the top-20% ranking): f5 Total Spend (uncorrelated with real category spend, rank-corr 0.01); f4/f21 rewards and f13–f16 benefit credits (real costs, but they barely move WHO is in the top 20%); f17/f18 lend line (capital cost, not revenue); f2/f12/f19/f20/f22/f23 (engagement/depth — not direct profit). id is never used.

## Profitability Equation
Each member's score is their estimated dollar contribution margin (NO percentile ranking). Each term is scaled by its own standard deviation so the weights express relative profit contribution on one footing; members flagged for collection-driven cancellation are then screened out of the profitable tier:

    base  = 0.738·z(f7) + 0.137·z(f10) + 0.348·z(f8) + 0.060·z(f6) + 0.060·z(f9)
            + 0.523·z(f1) + 0.110·z(−f11·f1)
    score = base,                          if f3 = 0  (member in good standing)
          = below the profitable tail,     if f3 = 1  (collection-driven cancellation → delinquency screen)

    where z(x) = x / std(x)

Every spend category carries a POSITIVE weight: all spend produces interchange revenue. The everyday categories (Other, Dining, Entertainment) earn the full net margin; the richer-reward travel categories (Airline, Lodging) earn a smaller positive margin because their points cost offsets more of the interchange — but they are not treated as losses. f1 (revolving balance → interest income) carries ~70% of the weight of the dominant spend category — interest is co-equal with spend. The collection screen is a business rule, not a tuned weight: a member in collections is not among the most profitable regardless of interest accrued, because the eventual loss and attrition dominate.

## Prediction Logic
The contribution-margin score is written as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% is the graded set. Members flagged for collection-driven cancellation (f3 = 1) — distressed and/or exiting, carrying ~5× the average default risk with essentially no spend — are screened out of the top tier even when their revolving-balance interest would otherwise rank them there. Members with no industry-spend breakdown (f6–f10 absent) earn no interchange by construction and score on revolving balance net of risk alone; arithmetically only a small fraction can clear the spend-driven cutoff, so ~1% of them remain in the top 20% — appropriate, since absence of a spend breakdown is itself associated with lower-value, higher-risk members. Deterministic (seed 42), reproducible from src/score_magnitude.py (dollar_profit_v15_allpos); never uses id.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. v15 retains industry spend across ALL categories and revolving balance as the two revenue engines, and uses RISKINESS fully: expected loss on the carried balance plus an explicit delinquency screen (f3, collection-driven cancellation), the clearest single credit-distress signal. Spend is taken at the industry-category level (the brief's "industry level spends"), not the f5 total, because f5 is uncorrelated with real category spend. All five categories are kept and signed positive because every dollar of spend earns interchange; travel categories simply earn less of it net of their richer rewards. Benefit utilization, rewards, and total-spend (f5) remain dropped because they do not move the top-tier ranking — keeping them would add unverifiable parameters without improving it.

## Coefficient/Weight Derivation
The revenue and expected-loss weights are anchored to our calibrated base: set by business reasoning (spend and interest are the two primary revenue engines; risk is the primary cost) and calibrated against the competition's public-leaderboard top-20%-overlap feedback. The dominant everyday-spend weight (Other) and the interest, entertainment, and expected-loss weights are unchanged from that calibration. The category MARGINS are signed by the card's reward economics: every category earns interchange (positive), and the 5×-reward travel categories (Airline, Lodging) carry a smaller positive net margin than the 1× everyday categories — an asymmetry in MAGNITUDE, not in sign. The delinquency screen is deliberately NOT a free parameter — it is the business rule "a member in collections is not top-profitable." Its effect was verified rather than tuned: of the members it removes from the top 20%, the overwhelming majority have no category spend and carry ~5× the population's average default risk; they are replaced by evidenced spenders. The screen therefore adds no overfitting surface.

## Feature Transformations
No percentile ranking of the final score. Each input term is scaled by its standard deviation (so a one-unit weight means one standard deviation of that driver) and combined linearly. Spend is decomposed into industry categories, each carrying its own positive signed weight. Expected loss is the product of the risk score and the balance exposure. Missing spend categories contribute zero (the member shows no spend there); f7 refunds are negative and net down correctly. The delinquency screen is a hard demotion of f3 = 1 members below the scored tail — it affects only WHO is in the top 20%, not the relative order of members in good standing.

## Business Logic
A member is profitable when their category-weighted spend plus net interest on revolving balance exceeds their expected credit loss. Three principles: (1) ALL SPEND IS REVENUE — every industry category earns interchange, so a high-volume spender is profitable even when their spend skews to richer-reward travel categories; those categories simply earn a thinner net margin, not a loss (penalizing them, as earlier variants did, wrongly demotes genuinely high-value spenders). (2) REVOLVING BALANCE is a first-class profit driver — interest income on a carried balance rivals the interchange on heavy spend, matching the issuer's actual P&L where lending margin and spend interchange are the two largest revenue lines. (3) a member flagged for COLLECTION-DRIVEN CANCELLATION is in financial distress and/or exiting the franchise, so their carried-balance interest is offset by elevated loss risk and a short remaining lifetime — they do not belong in the most-profitable quintile. High credit risk on a carried balance is the dominant cost and is subtracted.

## Assumptions
- Masked features are proxy-dollars; weights express relative profit contribution, scaled to comparable footing.
- Revolving balance (f1) proxies interest income (the data has no booked-interest field); it is a primary revenue pillar, co-equal with spend.
- Industry-category spend (f6–f10), not the f5 total, is the spend signal (f5 is uncorrelated with real spend, rank-corr 0.01).
- All spend categories earn net-positive interchange; the 5×-reward travel categories (Airline, Lodging) earn a smaller positive margin than everyday spend, but are not net-negative — so heavy spenders are not penalized for their category mix.
- f3 = 1 (collection-driven cancellation) marks a distressed/exiting member whose expected loss and attrition outweigh current interest revenue → excluded from the top tier. The removed members are overwhelmingly low-spend, so the screen's collateral on genuinely-profitable members is negligible.
- The absence of a spend breakdown signals a lower-value member; such members earn no interchange and rank on balance/risk only, so they are not promoted.
- The annual fee is constant and excluded; lend-line SIZE is a capital cost, not revenue (so f17/f18 are excluded).
- Risk acts on balance exposure (expected loss = risk × balance).

## Validation Approach
Label-free, full 500K, and built as a controlled change to a calibrated base. The ranking shares 80% of its top 20% with our calibrated best (Jaccard 0.80); the ~11% it reshuffles is a single, economically-isolated change — it stops penalizing 5×-reward travel spend, promoting high-volume travel-heavy spenders (median category spend ~$97K) over moderate-spend members. Because the change is grounded in card economics (all spend earns interchange) rather than fitted to the public split, and because the only prior variants that penalized travel spend underperformed, the direction is economically motivated. We do not claim the score's own shape proves correctness; whether all-positive category treatment improves top-20% overlap is decided by the leaderboard. The collection screen, validated separately, is retained unchanged.

## Additional Notes (Optional)
v15 keeps our validated core — the revolving-balance interest lever, the additive expected-loss term, and the collection-delinquency screen — and changes only the spend-category treatment: every industry category is net-positive interchange revenue, with travel categories earning a thinner (but still positive) margin, and lodging restored. It is the economic conclusion of an earlier finding that penalizing travel spend removed genuinely profitable high-volume members. If it improves on the prior best, all-positive category economics are confirmed; if not, the prior delinquency-screened ranking remains the locked fallback.
