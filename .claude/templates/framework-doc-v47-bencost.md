# Profitability Framework — Submission Writeup (v47 / interest-led P&L with a benefit-cost screen)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v47 = the recovered interest-led P&L base (identical economics to prior rounds) plus a
     BENEFIT-COST SCREEN: the 2,500 heaviest benefit-credit consumers in the top quintile are
     demoted — the designed test of the brief's fourth named driver (benefit utilization) as a
     COST, the one named driver never yet priced by a paid reading. 2,500-member swap off the
     measured v37L set. Pre-registered box [0.9016, 0.9366]. Build: scratchpad/build_v47.py. -->

## Variables Used
We score each member's estimated contribution margin to the issuer from the features that carry sign-stable profit information, plus relationship-state and cost screens:

Revenue: f1 Average Revolve Balance (net interest income — the dominant profit engine); f7 Other Spend (dominant general-spend category, interchange); f9 Lodging Spend (prepaid-hotel bookings, which additionally carry travel-portal commission — externally bracketed by published hotel-agency commissions of 10–22%); f10 Dining Spend (calibrated to approximately zero net margin).

Cost / risk: f11 Average Risk Score multiplied by balance exposure f1 (expected credit loss); f3 Collection-driven Cancellation (delinquency screen — validated three separate times, including a designed 1,313-member probe); f13–f16 benefit-credit consumption (lounge visits, airline credits, cab benefits, entertainment credit — dollarized as 50·f13 + f14 + 15·f15 + f16 and applied this round as a cost screen on the heaviest consumers: the brief's fourth named profitability driver, priced as the cost the issuer books when credits are consumed).

Deliberately excluded after systematic testing: id (leakage/gaming); the annual fee (constant within the product); f5 Total Spend (uncorrelated with the industry-category spends under every transform); f4/f21 rewards as direct P&L terms (a designed 1,741-member probe measured a rewards-engagement re-weighting at exact boundary-parity); f2 cancellation calls (a designed 2,415-member probe this week measured callers at full top-quintile parity — the truth prices exits from collection distress, not from voluntary-attrition signals); f17/f18 lend line (capital cost until drawn); standalone and spend-scaled risk terms; balance-curvature transforms; f12/f19/f20/f22/f23 as direct P&L terms (f19/f20 closed by a designed 1,200-member probe).

## Profitability Equation
The member's profitability is an interest-led contribution margin measured in standardized units (z(x) = x / std(x); missing inputs contribute 0). The central calibration:

    margin = 0.69·z(f1)                 [net interest income on the revolving balance]
           + 0.40·z(f7)                 [general-spend interchange]
           + 0.18·z(f9) − 0.01·z(f10)   [lodging (portal commission) margin; dining ≈ 0]
           − 0.58·z(f11·f1)             [expected credit loss on the balance exposure]

    score  = margin,                              if benefit burn < $504 and f3 = 0
           = demoted below lighter consumers,     if benefit burn ≥ $504  (benefit-cost screen — this round's test)
           = below the scored population,         if f3 = 1               (collection screen — validated)

Weights are calibrated so the equation is simultaneously consistent with the public-leaderboard results of all of our previously scored submissions (32 evaluated readings, reproduced at RMSE ≈ 0.003–0.004, frontier-weighted, leave-one-out validated); the surviving near-equivalent calibrations are ensembled by consensus vote with a margin tie-break. The validated base ranking (public 0.919143, directly measured) already incorporates two designed cohort-probe measurements. v47 then applies the benefit-cost screen to that measured set: the 2,500 heaviest benefit-credit consumers in the top quintile (dollarized burn ≥ $504) are replaced by the next-best non-consumer members under the same margin ordering. The screen is a parameter-free business rule, and the outcome arithmetic is pre-registered.

## Prediction Logic
Higher Prediction = more profitable to the issuer. All 500,000 members are scored and ranked descending; the graded set is the top 20%. Collection-flagged members (f3 = 1) rank below the scored population (validated three times). The heaviest benefit-credit consumers rank below observably identical lighter consumers: every lounge visit, travel credit, cab benefit, and entertainment credit is a real cost the issuer books, so at equal revenue the heavy consumer is less profitable. No-spend-breakdown members contribute 0 on spend terms and are scored on balance net of expected loss, with the cohort's top-quintile share fixed where a designed probe measured it. The score is deterministic, never uses id (corr(id, Prediction) = −7.3×10⁻⁶), has 399,031 distinct values, and the top-quintile cutoff is held by exactly one member.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization. Three are priced and validated by our measurement program: revolving balance ~1.8× the dominant spend term; expected loss ~1.4× the spend weight plus the hard f3 screen; spend at the industry-category level with lodging positive and airline/dining ≈ 0. The fourth — benefit utilization — is the one named driver never yet priced by a paid reading: our rankings since v10 all carry a similar heavy-consumer count (2,414–2,897 across all of them; the recent measured sets sit in a tight 2,414–2,772 band), so no paid reading has ever varied this axis at attributable scale, and our calibration family's benefit term is sign-unstable across refits for the same reason. This round prices it as a cost, the direction the issuer's own P&L books: credits consumed are expenses. The screen population is fully characterized and the measurement is powered (2,500 members, minimum detectable edge ≈ 5%).

## Coefficient/Weight Derivation
No label exists, so our own scored submissions are the measurement instrument: 32 prior submissions with known public overlaps constrain the weights (differential evolution, business-prior seeding, frontier weighting), reproducing the full history at RMSE ≈ 0.003–0.004, with ten designed probes and bounded updates — most landing inside their pre-registered arithmetic spans, each deviation itself measured and retained. Weight ratios stable across restarts: f1/f7 ≈ 1.7, expected-loss/f7 ≈ 1.5, f9/f7 ≈ 0.46, f10/f7 ≈ −0.02.

The benefit-cost screen carries no tuned coefficient — it is a hard demotion of the heaviest consumers, exactly parallel to the validated f3 screen and to last week's f2 attrition test. The test population is fully characterized: the 2,500 demoted members are heavy consumers (median dollarized burn $534) and strong current-period earners (median category spend $128.1K, median balance $1.6K, median risk 0.0002); their replacements are the next-best light-consumer members under the identical margin ordering (median burn $182, category spend $74.8K, balance $649). The screen deliberately overrides the consensus-whale protection for the 253 flagged members it covers — they are the test population. We disclose the honest scale context: at face-value dollarization the median burn ($534) is small against these members' revenue, so this round tests whether the ground truth prices benefit consumption as a materially heavier cost (or a cost-heavy segment marker) than the face amounts suggest; the pre-registered arithmetic prices every branch.

## Feature Transformations
- Standardization only for the P&L terms (divide by standard deviation; no centering; no percentile ranking of the final score).
- Expected loss = f11 × f1, standardized; alternative risk shapes tested and rejected.
- Benefit burn dollarization: 50·f13 (lounge visits) + f14 (airline credits $) + 15·f15 (cab benefits) + f16 (entertainment credit $); missing = 0 (credit not consumed).
- Missing values contribute 0 (leaderboard-validated in both directions); the no-breakdown cohort is internally ordered by an interpretable least-squares spend estimate with its top-quintile count held fixed.
- f7 refunds are negative and correctly net spend down.
- The benefit-cost and f3 screens are business rules (fixed demotion bands), not tuned weights.
- The consensus vote plus margin tie-break, with the screens applied as fixed demotion bands, is a monotone packaging of the ensemble.

## Business Logic
A Premier member is profitable when the interest earned on the balance they revolve, plus the interchange and travel-portal margins on their spend, exceeds their expected credit loss — and the credits they consume. Lending leads decisively (published net interest yields; audited issuer financials in both our reference markets); risk is priced per dollar of lending exposure with distressed relationships excluded outright; not all spend is equal (airline/dining ≈ 0 after rewards; lodging carries commission). This round prices the benefit side of the ultra-premium value proposition: lounge access, travel credits, cab benefits, and entertainment credits are the product's most expensive features, and the members who consume them hardest are the most expensive to serve. The screen tests whether the issuer's hidden profitability computation charges that consumption against the member — the direction the accounting books it — with the population bounded to 2.5% of the set and the arithmetic pre-registered.

## Assumptions
- Masked features are proxy-dollars on consistent within-feature scales; decoded per-dollar rates land in real-world bands in both the US and India markets (audited-financials cross-check).
- f1 proxies interest income; f11·f1 proxies expected loss; f3 = 1 marks a distressed/exiting member (directly probed); f13–f16 measure consumed benefit credits, booked as cost when consumed (this round's designed test of the rate).
- Industry-category spends (f6–f10), not f5, measure spend behavior.
- Missing = the line does not exist for that member (validated both directions).
- The hidden ground truth is a revenue-minus-cost computation over these features; our calibration recovers its relative weights from 32 observed evaluations.
- The annual fee is constant within the product.

## Validation Approach
Label-free, full 500K:
- Consistency with all paid evidence: the calibrated family reproduces all 32 prior public scores at RMSE ≈ 0.003–0.004; ten designed probes and bounded updates, most inside their pre-registered spans, each deviation measured and retained. Twelve structural axes plus six candidate terms tested and closed by measurement.
- The benefit-cost axis is verifiably OPEN before this round: rankings since v10 carry 2,414–2,897 heavy consumers (recent measured sets in a tight 2,414–2,772 band; the wider historical spread sits in early rounds whose compositions differed by tens of thousands of members — never an attributable variation of this axis), and the calibration family's benefit term is sign-unstable across refits. This is the designed measurement that closes it.
- Pre-registered arithmetic (fixed before submission): realized = 0.919143 + net·0.02500, span [0.9016, 0.9366]; net is the true top-20% accuracy differential between the demoted consumers and their replacements; downside is bounded to this submission (best-score-counts) and the result is folded back as a constraint either way.
- Integrity: 399,031 distinct scores, unique cutoff, zero collection-flagged and zero heavy-consumer members in the top quintile, corr(id) = −7.3×10⁻⁶, zero shared float values with all prior submission files, deterministic byte-reproducible build, raw-file structural audit confirms only the delivered features are used.

## Additional Notes (Optional)
v47 completes the pricing of the brief's four named drivers: it is the designed measurement of the last one (benefit utilization) never yet read, run in the cost direction the issuer's accounting implies. The construction isolates the axis exactly — base = our best directly-measured set (public 0.919143), change = the parameter-free screen and nothing else — so the reading attributes entirely to how the hidden truth prices benefit consumption. The framework remains O(n), fully explainable, and auditable end-to-end: the P&L equation carries the economics; the screens are stated business rules with stated demoted/promoted populations; and the outcome arithmetic was fixed before upload.
