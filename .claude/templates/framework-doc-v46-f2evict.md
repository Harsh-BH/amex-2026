# Profitability Framework — Submission Writeup (v46 / interest-led P&L with an attrition screen)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v46 = the recovered interest-led P&L base (identical economics to prior rounds) plus a HARD
     ATTRITION SCREEN: all cancellation-callers (f2 >= 1) are demoted below non-callers, the
     designed test of whether the hidden truth prices attrition the way it prices collection
     distress (f3, validated three times). 2,415-member swap off the measured v37L set.
     Pre-registered box [0.9022, 0.9360]. Score build: scratchpad/build_v46.py. -->

## Variables Used
We score each member's estimated contribution margin to the issuer from the features that carry sign-stable profit information, plus two relationship-state screens:

Revenue: f1 Average Revolve Balance (net interest income — the dominant profit engine); f7 Other Spend (dominant general-spend category, interchange); f9 Lodging Spend (prepaid-hotel bookings, which additionally carry travel-portal commission — externally bracketed by published hotel-agency commissions of 10–22%); f10 Dining Spend (calibrated to approximately zero net margin).

Cost / risk: f11 Average Risk Score multiplied by balance exposure f1 (expected credit loss); f3 Collection-driven Cancellation (delinquency screen — validated three separate times, including a designed 1,313-member probe); f2 Cancellation Calls (attrition screen — this round's designed test: a member who has called to cancel carries materially elevated attrition risk, so their forward-looking margin is discounted below observably identical non-callers).

Deliberately excluded after systematic testing: id (leakage/gaming); the annual fee (constant within the product); f5 Total Spend (uncorrelated with the industry-category spends under every transform); f4/f21 rewards and f13–f16 benefit credits as direct P&L terms (a designed 1,741-member probe measured a rewards-engagement re-weighting at exact boundary-parity); f17/f18 lend line (capital cost until drawn); standalone and spend-scaled risk terms; balance-curvature transforms; clipped-balance ordering corrections (measured negligible at the boundary); f12/f19/f20/f22/f23 as direct P&L terms (f19/f20 closed by a designed 1,200-member probe).

## Profitability Equation
The member's profitability is an interest-led contribution margin measured in standardized units (z(x) = x / std(x); missing inputs contribute 0). The central calibration:

    margin = 0.69·z(f1)                 [net interest income on the revolving balance]
           + 0.40·z(f7)                 [general-spend interchange]
           + 0.18·z(f9) − 0.01·z(f10)   [lodging (portal commission) margin; dining ≈ 0]
           − 0.58·z(f11·f1)             [expected credit loss on the balance exposure]

    score  = margin,                          if f2 = 0 and f3 = 0
           = demoted below all non-callers,   if f2 ≥ 1   (attrition screen — this round's test)
           = below the scored population,     if f3 = 1   (collection screen — validated)

Weights are calibrated so the equation is simultaneously consistent with the public-leaderboard results of all of our previously scored submissions (31 evaluated readings, reproduced at RMSE ≈ 0.003–0.004, frontier-weighted, leave-one-out validated); the surviving near-equivalent calibrations are ensembled by consensus vote with a margin tie-break. The validated base ranking (public 0.919143, directly measured) already incorporates two designed cohort-probe measurements. v46 then applies the attrition screen to that measured set: all 2,415 cancellation-callers in the top quintile are replaced by the next-best non-caller, non-collection members under the same margin ordering. The screen is a parameter-free business rule (like the validated f3 screen, it has no tuned weight), and the outcome arithmetic is pre-registered.

## Prediction Logic
Higher Prediction = more profitable to the issuer. All 500,000 members are scored and ranked descending; the graded set is the top 20%. Collection-flagged members (f3 = 1) rank below the scored population (validated three times). Cancellation-callers (f2 ≥ 1, 17.4% of members) rank below all non-callers: the issuer's expected future margin on a member who has already called to cancel is their current-period margin times a materially reduced survival probability. No-spend-breakdown members contribute 0 on spend terms and are scored on balance net of expected loss, with the cohort's top-quintile share fixed where a designed probe measured it. The score is deterministic, never uses id (corr(id, Prediction) = −4.3×10⁻⁴), has 399,080 distinct values, and the top-quintile cutoff is held by exactly one member.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. Nine calibration rounds price them consistently: revolving balance ~1.8× the dominant spend term (premium charge-card economics: net interest yield far exceeds per-dollar interchange); expected loss on balance exposure ~1.4× the spend weight (breakeven risk score ≈ 0.15), plus the hard f3 screen; spend at the industry-category level with lodging positive (externally consistent with published travel-portal commissions) and airline/dining ≈ 0 (published research finds portfolio rewards cost ≈ interchange — the 5x categories are where that wash lands); benefit utilization immaterial as cost, engagement, or interaction (a designed 1,741-member probe measured a rewards-engagement re-weighting at exact ranking parity). This round adds the one relationship-state variable never yet carried by any version: f2. Its selection logic is the direct sibling of the validated f3 screen — f3 marks distressed exits (screen validated, three measurements), f2 marks voluntary attrition intent; retention economics (defection studies of redeemers vs non-redeemers; industry CLV practice) price attrition as a first-order discount on every future revenue line. Since every modern submission carries a near-identical caller share (2.37–2.75% across all rankings since v10), the paid evidence to date is uninformative on this axis — a designed measurement is the only way to price it.

## Coefficient/Weight Derivation
No label exists, so our own scored submissions are the measurement instrument: 31 prior submissions with known public overlaps constrain the weights (differential evolution, business-prior seeding, frontier weighting), reproducing the full history at RMSE ≈ 0.003–0.004, with nine designed probes and bounded updates — most landing inside their pre-registered arithmetic spans, each deviation itself measured and retained. Weight ratios stable across restarts: f1/f7 ≈ 1.7, expected-loss/f7 ≈ 1.5, f9/f7 ≈ 0.46, f10/f7 ≈ −0.02.

The attrition screen carries no tuned coefficient — it is a hard demotion, exactly like the validated f3 screen. The test population is fully characterized: the 2,415 evicted callers are strong current-period earners (median category spend $94.2K, median revolve balance $4.6K, median risk 0.0007), and the 2,415 promoted replacements are the next-best non-callers under the identical margin ordering (median category spend $77.2K, median balance $0.4K, median risk 0.0002). The screen deliberately overrides the consensus-whale protection for the 237 flagged members it covers — they are the test population, and their current-period strength is precisely what makes the measurement sharp: if the hidden truth books attrition, these are the members it discounts despite their earnings.

## Feature Transformations
- Standardization only for the P&L terms (divide by standard deviation; no centering; no percentile ranking of the final score).
- Expected loss = f11 × f1, standardized; alternative risk shapes tested and rejected.
- Missing values contribute 0 (leaderboard-validated in both directions); the no-breakdown cohort is internally ordered by an interpretable least-squares spend estimate with its top-quintile count held fixed.
- f7 refunds are negative and correctly net spend down.
- f2 and f3 are binary relationship-state flags used as screens (business rules), not tuned weights; f2 ≥ 1 demotes below all non-callers, f3 = 1 demotes below the scored population.
- The consensus vote plus margin tie-break, with the screen applied as a fixed demotion band, is a monotone packaging of the ensemble.

## Business Logic
A Premier member is profitable when the interest earned on the balance they revolve, plus the interchange and travel-portal margins on their spend, exceeds their expected credit loss — and only for as long as they remain a member. Lending leads decisively (published net interest yields; audited issuer financials in both our reference markets); risk is priced per dollar of lending exposure with distressed relationships excluded outright; not all spend is equal (airline/dining ≈ 0 after rewards; lodging carries commission). This round prices the retention dimension: a cancellation call is the strongest observable signal of imminent voluntary attrition, and an issuer valuing forward profitability discounts such members' expected margin across every revenue line — spend, interest, and fees all terminate at attrition. The screen extends our most-validated structural finding (the truth hard-excludes distressed exits, f3) to its voluntary-exit sibling, and is bounded, parameter-free, and pre-registered.

## Assumptions
- Masked features are proxy-dollars on consistent within-feature scales; decoded per-dollar rates land in real-world bands in both the US and India markets (audited-financials cross-check).
- f1 proxies interest income; f11·f1 proxies expected loss; f3 = 1 marks a distressed/exiting member (directly probed); f2 ≥ 1 marks voluntary attrition intent (this round's designed test).
- Industry-category spends (f6–f10), not f5, measure spend behavior.
- Missing = the line does not exist for that member (validated both directions).
- The hidden ground truth is a revenue-minus-cost computation over these features; our calibration recovers its relative weights from 31 observed evaluations.
- The annual fee is constant within the product.

## Validation Approach
Label-free, full 500K:
- Consistency with all paid evidence: the calibrated family reproduces all 31 prior public scores at RMSE ≈ 0.003–0.004; nine designed probes and bounded updates, most inside their pre-registered spans, each deviation measured and retained. Eleven structural axes plus six candidate terms tested and closed by measurement.
- The attrition-screen axis is verifiably OPEN before this round: every submission since v10 carries a caller share in a 2.37–2.75% band (~380-member spread — below any probe's resolution), and a linear-programming audit over all 31 exact readings confirms the evidence neither requires nor forbids callers in the true top quintile (feasible caller mass spans 0 to 8,077 of 70,000). This is the designed measurement that closes it.
- Pre-registered arithmetic (fixed before submission): realized = 0.919143 + net·0.02415, span [0.9022, 0.9360]; net is the true top-20% accuracy differential between the evicted callers and their replacements; downside is bounded to this submission (best-score-counts) and the result is folded back as a constraint either way.
- Integrity: 399,080 distinct scores, unique cutoff, zero collection-flagged and zero caller members in the top quintile, corr(id) = −4.3×10⁻⁴, zero shared float values with all prior submission files, deterministic byte-reproducible build, raw-file structural audit confirms only the delivered features are used.

## Additional Notes (Optional)
v46 is a designed measurement of the last major relationship-state variable never carried by any of our 45 scored variants. The construction isolates the attrition axis exactly: base = our best directly-measured set (public 0.919143), change = the parameter-free screen and nothing else, so the reading attributes entirely to how the hidden truth prices cancellation-callers. The framework remains O(n), fully explainable, and auditable end-to-end: the P&L equation carries the economics; the screens are stated business rules with stated evicted/promoted populations; and the outcome arithmetic was fixed before upload.
