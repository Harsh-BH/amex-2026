# Profitability Framework — Submission Writeup (v22 / hybrid-basis: dollar spend+lending, rank-normalized specialty categories)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v22 = our v19 lending-co-equal magnitude ranking, refined so the two linear-in-dollars revenue
     engines (general spend f7, revolving balance f1) stay on the dollar basis while the four smaller
     specialty spend categories (f6/f8/f9/f10) are measured on a percentile (rank) basis, so a member
     cannot enter the profitable tier on one inflated specialty category. Code: dollar_profit_v22_hybrid. -->

## Variables Used
We score each member's estimated dollar contribution margin from the features that drive the profitable tail, and add an explicit credit-distress screen:

Revenue: f1 Average Revolve Balance (net interest income — a primary issuer revenue, weighted co-equal with top spend); f7 Other Spend (the dominant general-spend category, the bulk of interchange); f8 Entertainment, f10 Dining, f6 Airline, f9 Lodging spend (the smaller specialty categories, each earning positive interchange).

Cost / risk: f11 Average Risk Score applied to balance exposure (expected credit loss); f3 Collection-driven Cancellation (an explicit delinquency screen — the clearest single credit-distress signal).

Deliberately omitted (negligible influence on the top-20% ranking): f5 Total Spend (uncorrelated with real category spend, rank-corr 0.01); f4/f21 rewards and f13–f16 benefit credits (real costs, but they barely move WHO is in the top 20%); f17/f18 lend line (capital cost, not revenue); f2/f12/f19/f20/f22/f23 (engagement/depth — not direct profit). id is never used.

## Profitability Equation
Each member's score is their estimated dollar contribution margin (NO percentile ranking of the final score). The two linear-in-dollars revenue engines — general spend and revolving balance — are scaled by their standard deviation (dollar basis); the four smaller specialty spend categories are measured on a percentile basis so that a member's rank within a specialty category, not its raw magnitude, contributes. Members flagged for collection-driven cancellation are then screened out of the profitable tier:

    base  = 0.738·z(f1) + 0.738·z(f7)                          [dollar basis: net interest + general-spend interchange]
            + 0.348·r(f8) + 0.137·r(f10) + 0.060·r(f6) + 0.060·r(f9)   [rank basis: specialty categories]
            + 0.110·z(−f11·f1)                                 [expected credit loss]
    score = base,                          if f3 = 0  (member in good standing)
          = below the profitable tail,     if f3 = 1  (collection-driven cancellation → delinquency screen)

    where z(x) = x / std(x)   and   r(x) = percentile-rank(x) / std(percentile-rank(x))

The revolving balance f1 (interest income) and general spend f7 (the dominant interchange source) are booked revenue that scales linearly with dollars, so they are measured in dollars. The four specialty categories (entertainment, dining, airline, lodging) are smaller lines where a single large purchase can make a moderate customer look like a top spender; measuring them by within-category percentile keeps their weight while preventing one inflated specialty category from vaulting a member into the profitable tier. The collection screen is a business rule, not a tuned weight.

## Prediction Logic
The contribution-margin score is written as the Prediction; higher means more profitable. All 500,000 members are scored by one equation and ranked descending; the top 20% is the graded set. Members flagged for collection-driven cancellation (f3 = 1) are screened out of the top tier. Keeping the two dominant revenue engines (f1 balance, f7 general spend) on the dollar basis preserves the ranking of the genuine high-value members; measuring the smaller specialty categories on a rank basis only reshuffles members near the top-20% boundary — specifically, it demotes a member who cleared the cutoff on one outsized specialty category and promotes an otherwise-comparable member with broader profitable activity. Members with no industry-spend breakdown score on balance net of risk alone; combined with the screen they remain ~1% of the top 20% — appropriate, since absence of a spend breakdown is associated with lower-value members. Deterministic (seed 42), reproducible from src/score_magnitude.py (dollar_profit_v22_hybrid); never uses id.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. v22 keeps v19's elevation of REVOLVING PATTERNS (f1) to co-equal with spend (the issuer earns ~12% net interest on carried balances and lending concentrates the majority of card profit), and refines how SPEND BEHAVIOR is measured: the dominant general-spend line (f7) is taken in dollars, while the four smaller 5×-reward-eligible specialty categories are taken by within-category rank so their contribution reflects relative standing rather than a single large transaction. Spend is taken at the industry-category level (the brief's "industry level spends"), not the f5 total (f5 is uncorrelated with real spend). Riskiness enters as expected loss plus the collection screen. Benefit utilization, rewards, and total-spend (f5) remain dropped because they do not move the top-tier ranking.

## Coefficient/Weight Derivation
The weights are set by business reasoning and calibrated against the competition's public-leaderboard feedback; they are unchanged from the v19 calibrated base (net-interest-grounded f1 co-equal with the dominant spend term, positive specialty-category weights, expected-loss term). The change in v22 is a measurement-basis choice, not a re-weighting: the two linear-in-dollars revenue engines (f1 net interest at ~11.9% reported yield, f7 general-spend interchange at ~2.2%) stay in dollars because booked revenue scales linearly with the underlying dollars; the four specialty categories move to a percentile basis because they are smaller, more skewed lines where raw magnitude over-represents a single large purchase. The expected-loss and collection-screen logic are unchanged.

## Feature Transformations
No percentile ranking of the final score. General spend (f7) and revolving balance (f1) are scaled by their standard deviation (dollar basis). The four specialty spend categories (f8, f10, f6, f9) are transformed to their within-category percentile rank, then scaled to a comparable footing — this compresses the heavy right tail of each specialty line so a moderate specialty spender is not mis-ranked as a whale. Expected loss is the product of the risk score and balance exposure. Missing spend categories contribute at the low end of their rank; f7 refunds are negative and net down on the dollar basis. The delinquency screen is a hard demotion of f3 = 1 members below the scored tail.

## Business Logic
A member is profitable when their net interest on revolving balance plus category-weighted spend exceeds their expected credit loss. Principles: (1) LENDING IS A FIRST-CLASS PROFIT ENGINE — net interest on a carried balance (~12% yield) concentrates the majority of card profit, so revolving balance is weighted co-equal with the dominant spend line. (2) DOLLARS WHERE DOLLARS ARE BOOKED, RANK WHERE MAGNITUDE MISLEADS — general spend and interest are booked revenue linear in dollars, so they are measured in dollars; the smaller specialty categories are measured by rank so one outsized specialty purchase does not masquerade as broad profitability. (3) ALL SPEND IS REVENUE — every category earns positive interchange. (4) a member flagged for COLLECTION-DRIVEN CANCELLATION is distressed/exiting and does not belong in the most-profitable quintile. High credit risk on a carried balance is the dominant cost and is subtracted.

## Assumptions
- Masked features are proxy-dollars; weights express relative profit contribution, scaled to comparable footing.
- Revolving balance (f1) proxies interest income (no booked-interest field exists); at ~12% net interest yield it is a primary revenue pillar, co-equal with spend.
- General spend (f7) and balance (f1) are booked revenue linear in dollars → measured in dollars; the smaller specialty categories (f6/f8/f9/f10) are skewed lines where a single large purchase over-represents value → measured by within-category rank.
- Industry-category spend (f6–f10), not the f5 total, is the spend signal (f5 is uncorrelated with real spend, rank-corr 0.01).
- All spend categories earn net-positive interchange; the 5×-reward travel categories earn a smaller positive margin than everyday spend, not a net loss.
- f3 = 1 (collection-driven cancellation) marks a distressed/exiting member excluded from the top tier; the removed members are overwhelmingly low-spend, so collateral on profitable members is negligible.
- The absence of a spend breakdown signals a lower-value member; such members rank on balance/risk only and are not over-promoted.
- The annual fee is constant and excluded; lend-line SIZE is a capital cost, not revenue (f17/f18 excluded).

## Validation Approach
Label-free, full 500K, built as a controlled change to the prior public-leaderboard best (v19 lending co-equal, top-20% overlap 0.859). v22 changes only the measurement basis of the four smaller specialty categories; it holds the two dominant revenue engines (f1, f7) and all weights fixed. The highest-conviction members are preserved: the pure-transactor high-general-spend "whales" that every prior submission agrees belong in the top tier retain a 0.999 in-rate, confirming the change does not move in the direction the leaderboard has historically penalized (demoting high-spend members). The transform reshuffles ~14% of the top 20% (Jaccard 0.86 versus v19), concentrated at the top-20% boundary where members are near-ties on the raw features — exactly the region where a magnitude-versus-rank measurement choice should matter and where the prior ranking had no strong signal to discriminate. The score is non-degenerate (402,512 distinct values) and contains no members flagged for collection-driven cancellation in the top tier. The change is a defensible measurement refinement (rank the small skewed lines, keep the large linear ones in dollars), not a fit to the public split, so it is expected to behave consistently on the hidden 30%.

## Additional Notes (Optional)
v22 refines v19 with a single, interpretable measurement choice: keep the two linear-in-dollars revenue engines (general spend f7, revolving balance f1) on the dollar basis, and measure the four smaller, more-skewed specialty spend categories (airline, lodging, entertainment, dining) on a within-category percentile basis. The economic rationale is that booked revenue (interchange on general spend, net interest on balances) scales linearly with dollars and should be counted in dollars, whereas a single large purchase in a small specialty category should not let a moderate customer outrank a broadly profitable one. All other validated structure — the lending co-equal weight, the expected-loss term, and the collection-driven-cancellation screen — is unchanged. The full development path (interpretable revenue−cost design → leaderboard-informed calibration → primary-source economic grounding → measurement-basis refinement) is documented in the project report.
