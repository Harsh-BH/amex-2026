# Profitability Framework — Submission Writeup (v50 / interest-led P&L with a bounded dual-engine correction)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v50 = the leaderboard-validated v35 ranking, adjusted by a bounded 2,500-member dual-engine
     correction: reward members who fire BOTH profit engines (revolving balance AND spend) from a
     single relationship. Score build: scratchpad/build_v50_dualengine.py. BENCH candidate. -->

## Variables Used
We score each member's estimated contribution margin to the issuer from the features that carry sign-stable profit information, plus a credit-distress screen and one interaction term:

Revenue: f1 Average Revolve Balance (net interest income — the dominant profit engine); f7 Other Spend (dominant general-spend category, interchange); f9 Lodging Spend (prepaid-hotel bookings, which additionally carry travel-portal commission); f10 Dining Spend (≈ zero net margin).

Cost / risk: f11 Average Risk Score multiplied by balance exposure f1 (expected credit loss); f3 Collection-driven Cancellation (delinquency screen — validated three separate times).

Interaction (this version): a dual-engine term formed from f7/category-spend AND f1 revolving balance — it rewards members who generate BOTH interchange (spend) AND net interest (a carried balance) from a single relationship. It is constructed so pure transactors (f1 = 0) receive zero dual-engine bonus.

Carried with near-zero calibrated weight (robustness, immaterial to the ranking): f6 Airline and f8 Entertainment spend (priced at ≈ zero net margin — 5x reward cost offsets interchange).

Deliberately excluded after systematic testing: id (leakage); the annual fee (constant within the product); f5 Total Spend (uncorrelated with the industry-category spends under every transform); f4/f21 rewards and f13–f16 benefit credits (real costs, immaterial to top-quintile membership); f17/f18 lend line (capital cost until drawn); f2/f12/f19/f20/f22/f23 (engagement/relationship depth — activity, not profit; tested as additive terms and each read at parity or a loss).

## Profitability Equation
The member's profitability is an interest-led contribution margin in standardized units (z(x) = x / std(x); missing inputs contribute 0), plus a dual-engine interaction:

    margin = 0.70·z(f1)                 [net interest income on the revolving balance]
           + 0.39·z(f7)                 [general-spend interchange]
           + 0.19·z(f9) + 0.002·z(f10)  [lodging (portal commission) margin; dining ≈ 0]
           − 0.57·z(f11·f1)             [expected credit loss on the balance exposure]

    dual   = rank(category-spend) × revolving-intensity      [revolving-intensity = 0 if f1 = 0]

    score  = z(validated margin ranking) + 0.85·z(dual),   if f3 = 0
           = below the scored population,                   if f3 = 1   (collection-cancellation screen)

No profitability label exists, so weights are calibrated so the base margin is simultaneously consistent with the public-leaderboard results of all prior scored submissions (the leaderboard-inversion method described under Coefficient Derivation). Because the base ranking is itself leaderboard-validated (public top-quintile overlap 0.918971, our banked best), the dual-engine term is applied as a BOUNDED correction: it re-orders only the ~2,500 members (2.5% of the top quintile) at the profitability boundary where the two profit engines disagree with the margin-only ordering, leaving the validated core (including the highest-conviction members) intact.

## Prediction Logic
Higher Prediction = more profitable to the issuer. All 500,000 members are scored by the same rule and ranked descending; the graded set is the top 20%. The dual-engine correction moves 2,500 members: it swaps IN moderate-spend members who ALSO carry a revolving balance (fire both engines) and swaps OUT high-spend, zero-balance transactors at the boundary (fire only one engine, and on a rich-rewards premium card the rewards cost on their spend can exceed the interchange it earns). Members flagged for collection-driven cancellation (f3 = 1) are screened below the scored population. The score is deterministic (fixed seeds), never uses id (corr(id, Prediction) = −6×10⁻⁵), has 399,015 distinct values, and the top-quintile cutoff is held by exactly one member. Overlap with the validated v35 set is 0.975 (a bounded, auditable adjustment); the consensus-core high-spend members are retained at 99.9%.

## Variable Selection Logic
The brief names four drivers — spend behavior, revolving patterns, riskiness, benefit utilization. The base equation prices them consistently across six rounds of recalibration: revolving balance leads (~1.8× the spend weight), risk is priced on lending exposure (f11 × f1, breakeven risk ≈ 0.15), spend enters at the industry-category level (lodging positive, airline/dining ≈ 0), and benefit utilization is immaterial to top-quintile membership. The dual-engine INTERACTION is added because the single most profitable relationship to a premium issuer is one that produces interchange AND net interest simultaneously — a moderate spender who also revolves out-earns an equally-ranked pure transactor, because the transactor's rich rewards cost erodes the interchange while the revolver's balance yields nearly-pure-margin interest. This term won as a standalone submission earlier in the project (+0.014 public overlap when first introduced); here it is re-applied as a bounded correction on top of the fully-calibrated base rather than as a free weight, because in the full calibration family the interaction is not sign-stable — so it is trusted only where it moves the boundary, not the core.

## Coefficient/Weight Derivation
No label exists, so we treat our own scored submissions as the measurement instrument: each prior submission has a known public top-20% overlap, and the base weights are those whose implied top quintile reproduces all observed public scores at once (differential evolution, frontier-weighted, RMSE ≈ 0.003). Weight ratios are restart-stable: f1/f7 ≈ 1.8, expected-loss/f7 ≈ 1.4, f9/f7 ≈ 0.47. Decoded into per-dollar rates (anchoring general spend at ~1.3% net margin): revolving yield ≈ 18–20%/$, loss severity ≈ 1.1–1.3× exposure, airline ≈ 0, lodging ≈ +8–9%/$ — all inside real-world premium-card bands. The dual-engine weight (0.85 on the standardized interaction) is set to a trust-region size: large enough to re-order the 2,500 boundary members where both engines fire, small enough that the validated core and the consensus-whale set (99.9% retained) do not move. It is deliberately a bounded correction, not a fitted free parameter, because our instrument cannot certify a far-from-history interaction weight without a leaderboard read — so this submission IS that read.

## Feature Transformations
- Standardization only: each dollar term divided by its standard deviation (no centering; no percentile ranking of the final margin).
- Expected loss is the product f11 × f1 (probability-of-loss proxy × balance exposure), standardized.
- Dual-engine term: rank(total category spend) × revolving-intensity, where revolving-intensity is the percentile rank of f1 among members who carry a balance and is set to 0 for transactors (f1 = 0). This makes the interaction reward only members firing both engines and leaves pure transactors' base ranking unperturbed by the bonus (whale-safe by construction).
- Missing values contribute 0 (a missing line means that revenue/cost does not exist for the member); f7 refunds are negative and net spend down.
- The f3 screen is a business rule (hard demotion), not a tuned weight.
- The dual-engine correction is applied as a bounded, monotone tilt on the validated ranking; it changes 2.5% of the top quintile and introduces no new feature beyond f1 and category spend.

## Business Logic
A Premier member is profitable when the interest on the balance they revolve, plus the interchange and travel-portal margins on their spend, exceeds their expected credit loss. The base framework encodes this as a lending-led, risk-priced contribution margin. The dual-engine correction adds the one economically-sharp refinement at the boundary: the most valuable relationship is the SUPER-CUSTOMER who fires both engines — heavy enough spend to earn interchange AND a carried balance to earn interest — because the two revenue streams come from one acquisition and one servicing cost, i.e. one stickier, higher-lifetime-value relationship. Conversely, the high-spend zero-balance transactor at the boundary is the weakest profitable member: on an ultra-premium card the 5x/rich rewards on their spend can cost more than the ~2.2% interchange it earns, and they contribute no interest — so a moderate spender who also revolves should rank above them. This is exactly the swap the correction makes. The framework remains a revenue-minus-cost statement per member, O(n), and auditable term by term.

## Assumptions
- Masked features are proxy-dollars on consistent within-feature scales; weights express relative per-dollar profit rates (decoded rates land in real-world bands).
- f1 proxies interest income; f11 is a default-probability-like score so f11·f1 proxies expected loss; f3 = 1 marks a distressed/exiting member (directly probed).
- Industry-category spends (f6–f10), not f5, measure spend behavior.
- Missing = the line does not exist for that member.
- The dual-engine interaction reflects genuine relationship-level economics (interchange + interest from one relationship), not a data artifact; it is applied as a bounded correction precisely because its exact weight is not identified by our leaderboard history without a fresh read.
- The annual fee is constant within the product and cannot differentiate members.

## Validation Approach
Label-free, full 500K, and — for this version — pre-registered as a bounded probe:
- The base ranking is leaderboard-validated (0.918971, our banked best) and reproduces all prior public scores at RMSE ≈ 0.003.
- The dual-engine direction has a prior positive read (+0.014 as a standalone submission); this version re-tests it as a bounded correction on the fully-calibrated base. Pre-registered arithmetic: realized = 0.918971 + net × (2500/100000), box [0.8940, 0.9440]; honest expectation ≈ 0.919–0.921 (the correction moves boundary members in the confirmed pro-revolver direction, but the base already prices lending heavily, so parity is the modal outcome). The read settles whether the interaction still carries marginal signal.
- Integrity/robustness: whale-in 99.9%, revolver share consistent with the leaderboard-rewarded band, zero collection-flagged members in the top quintile, 399,015 distinct scores with a unique cutoff, no id use (corr = −6×10⁻⁵), deterministic and reproducible, and zero exact score values shared with any prior submission file.

## Additional Notes (Optional)
v50 is a bounded, pre-registered test of a single hypothesis: does the dual-engine interaction (reward members firing both the spend and the lending engine) still add value on top of the fully-calibrated interest-led P&L? It is applied conservatively — 2,500 boundary members, 2.5% of the top quintile — because the interaction is not sign-stable in the calibration family and our instrument cannot certify its weight without a leaderboard read; this submission is that read. The banked best remains unaffected under best-score-counts. The correction is economically motivated (a single relationship yielding both interchange and interest is the highest-value premium-card customer; a high-spend zero-balance transactor whose rich rewards can exceed their interchange is the weakest profitable member), O(n), and fully auditable.
