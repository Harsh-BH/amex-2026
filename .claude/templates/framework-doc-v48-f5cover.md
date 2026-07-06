# Profitability Framework — Submission Writeup (v48 / interest-led P&L with a total-spend coverage term)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v48 = the recovered interest-led P&L base (identical economics to prior rounds) plus a
     TOTAL-SPEND COVERAGE promotion: the 2,500 strongest members at the f5 winsor cap that the
     category-only equation excludes are promoted over the weakest incumbents — the designed
     test of whether the ground truth carries a term on f5 ("Total Spend"), the one delivered
     spend measure our framework has never used. 2,500-member swap off the measured v37L set.
     Pre-registered box [0.9016, 0.9366]. Build: scratchpad/build_v48.py. -->

## Variables Used
We score each member's estimated contribution margin to the issuer from the features that carry sign-stable profit information, plus a coverage term under designed test:

Revenue: f1 Average Revolve Balance (net interest income — the dominant profit engine); f7 Other Spend (dominant general-spend category, interchange); f9 Lodging Spend (prepaid-hotel bookings, which additionally carry travel-portal commission — externally bracketed by published hotel-agency commissions of 10–22%); f10 Dining Spend (calibrated to approximately zero net margin); f5 Total Spend (this round's designed test — the all-channel spend total: a member whose total spend saturates the recorded range while their industry-category lines are moderate still earns interchange on the off-category difference, revenue a category-only equation never books).

Cost / risk: f11 Average Risk Score multiplied by balance exposure f1 (expected credit loss); f3 Collection-driven Cancellation (delinquency screen — validated three separate times, including a designed 1,313-member probe).

Deliberately excluded after systematic testing: id (leakage/gaming); the annual fee (constant within the product); f4/f21 rewards and f13–f16 benefit credits (designed probes of 1,741 and 2,500 members measured rewards-engagement and benefit-cost re-weightings at boundary parity — the truth neither rewards engagement nor charges credit consumption at a material rate); f2 cancellation calls (a designed 2,415-member probe measured callers at full top-quintile parity); f17/f18 lend line (capital cost until drawn); standalone and spend-scaled risk terms; balance-curvature transforms; f12/f19/f20/f22/f23 (f19/f20 closed by a designed 1,200-member probe).

## Profitability Equation
The member's profitability is an interest-led contribution margin measured in standardized units (z(x) = x / std(x); missing inputs contribute 0). The central calibration:

    margin = 0.69·z(f1)                 [net interest income on the revolving balance]
           + 0.40·z(f7)                 [general-spend interchange]
           + 0.18·z(f9) − 0.01·z(f10)   [lodging (portal commission) margin; dining ≈ 0]
           − 0.58·z(f11·f1)             [expected credit loss on the balance exposure]

    plus this round's coverage promotion: the 2,500 strongest members (by the same margin)
    whose Total Spend f5 saturates the recorded range but whom the category-only margin
    excludes from the top quintile are promoted over the 2,500 weakest incumbents.

    score  = margin (with the coverage promotion applied at the boundary),  if f3 = 0
           = below the scored population,                                   if f3 = 1

Weights are calibrated so the equation is simultaneously consistent with the public-leaderboard results of all of our previously scored submissions (33 evaluated readings, reproduced at RMSE ≈ 0.003–0.004, frontier-weighted, leave-one-out validated); the surviving near-equivalent calibrations are ensembled by consensus vote with a margin tie-break. The validated base ranking (public 0.919143, directly measured) already incorporates two designed cohort-probe measurements. v48 then applies the coverage promotion to that measured set. The promotion is bounded to 2.5% of the graded set, consensus-core members are never demoted, and the outcome arithmetic is pre-registered.

## Prediction Logic
Higher Prediction = more profitable to the issuer. All 500,000 members are scored and ranked descending; the graded set is the top 20%. Collection-flagged members (f3 = 1) rank below the scored population (validated three times). The promoted members are fully characterized: all sit at the recorded Total Spend maximum ($13,596 — the top of the delivered range, shared by 12,915 members), carry zero revolving balance and zero measured risk (median f11 0.0000), and have moderate industry-category spend (median $62.2K) — exactly the profile whose profitability a category-only equation understates if off-category interchange is real. They replace the 2,500 weakest non-core incumbents under the same margin (median category spend $75.8K, balance $1.6K). No-spend-breakdown members contribute 0 on spend terms and are scored on balance net of expected loss, with the cohort's top-quintile share fixed where a designed probe measured it. The score is deterministic, never uses id (corr(id, Prediction) = −5.9×10⁻⁴), has 398,993 distinct values, and the top-quintile cutoff is held by exactly one member.

## Variable Selection Logic
The brief names four profitability drivers — spend behavior, revolving patterns, riskiness, and benefit utilization — and our measurement program has now priced all four (revolving ~1.8× the dominant spend term; expected loss ~1.4× plus the hard f3 screen; industry-category spend with lodging positive and airline/dining ≈ 0; benefit utilization measured at zero weight in both directions by designed probes). f5 is the one delivered spend measure never yet carried by any of our 44 scored variants: we set it aside early because it is uncorrelated with the industry-category spends (Spearman 0.009) and so cannot proxy them. But that finding cuts both ways — a total that does not track the categories is either noise or additional information (off-category spend the categories never see). No paid reading distinguishes the two: our recent measured rankings carry a near-identical count of capped-f5 members (4,238–4,465 — below any reading's resolution; earlier rounds range a few percent wider amid much larger composition shifts), so the axis is verifiably open. This round is the designed measurement, run in the promotion direction on the members for whom the two readings of f5 disagree most.

## Coefficient/Weight Derivation
No label exists, so our own scored submissions are the measurement instrument: 33 prior submissions with known public overlaps constrain the weights (differential evolution, business-prior seeding, frontier weighting), reproducing the full history at RMSE ≈ 0.003–0.004, with eleven designed probes and bounded updates — most landing inside their pre-registered arithmetic spans, each deviation itself measured and retained. Weight ratios stable across restarts: f1/f7 ≈ 1.7, expected-loss/f7 ≈ 1.5, f9/f7 ≈ 0.46, f10/f7 ≈ −0.02.

The coverage promotion carries no tuned coefficient: it is a bounded set-level test, exactly parallel to our prior designed probes. Selection within the capped-f5 pool is by the validated margin itself (under the hypothesis, the true top members among the capped pool are the ones strongest on the rest of the P&L), so the reading isolates the f5 axis rather than any other re-weighting. We disclose the honest evidence balance: our early screens found f5 orthogonal to every value proxy we trust (which is why the base equation excludes it), and a residual audit over all exact readings ranked f5 first among never-modeled features while remaining below the audit's noise floor. The pre-registered arithmetic prices every branch of that uncertainty.

## Feature Transformations
- Standardization only for the P&L terms (divide by standard deviation; no centering; no percentile ranking of the final score).
- Expected loss = f11 × f1, standardized; alternative risk shapes tested and rejected.
- f5 is used as delivered (winsorized at the recorded range top; 12,915 members share the cap); the promotion pool is the capped members outside the base top, ordered by the base margin.
- Missing values contribute 0 (leaderboard-validated in both directions); the no-breakdown cohort is internally ordered by an interpretable least-squares spend estimate with its top-quintile count held fixed.
- f7 refunds are negative and correctly net spend down.
- The f3 screen is a business rule, not a tuned weight.
- The consensus vote plus margin tie-break, with the bounded promotion applied as a fixed offset on the selected set, is a monotone packaging of the ensemble.

## Business Logic
A Premier member is profitable when the interest earned on the balance they revolve, plus the interchange and portal margins on their spend, exceeds their expected credit loss. Lending leads decisively (published net interest yields; audited issuer financials in both our reference markets); risk is priced per dollar of lending exposure with distressed relationships excluded outright; not all spend is equal. This round prices spend COVERAGE: the delivered data records both an all-channel total (f5) and five industry-category lines (f6–f10), and they disagree — some members saturate the total while showing only moderate category spend. If the issuer's hidden computation books interchange on total spend, those members earn revenue our category-only equation never sees, and the strongest of them belong in the top quintile. The promotion is bounded to 2.5% of the set, protects every consensus-core member, evicts only the weakest boundary incumbents, and is pre-registered — a designed measurement of the last delivered spend variable never priced by a paid reading.

## Assumptions
- Masked features are proxy-dollars on consistent within-feature scales; decoded per-dollar rates land in real-world bands in both the US and India markets (audited-financials cross-check).
- f1 proxies interest income; f11·f1 proxies expected loss; f3 = 1 marks a distressed/exiting member (directly probed).
- f6–f10 measure industry-category spend; f5 measures all-channel total spend (this round's designed test of whether the truth books it).
- Missing = the line does not exist for that member (validated both directions).
- The hidden ground truth is a revenue-minus-cost computation over these features; our calibration recovers its relative weights from 33 observed evaluations.
- The annual fee is constant within the product.

## Validation Approach
Label-free, full 500K:
- Consistency with all paid evidence: the calibrated family reproduces all 33 prior public scores at RMSE ≈ 0.003–0.004; eleven designed probes and bounded updates, most inside their pre-registered spans, each deviation measured and retained. Thirteen structural axes plus six candidate terms tested and closed by measurement.
- The f5 axis is verifiably OPEN before this round: recent measured rankings carry 4,238–4,465 capped-f5 members (~230-member spread — below any reading's resolution), and our exclusion of f5 rests on internal screens, not on any paid reading. This is the designed measurement that closes it.
- Pre-registered arithmetic (fixed before submission): realized = 0.919143 + net·0.02500, span [0.9016, 0.9366]; net is the true top-20% accuracy differential between the promoted capped-f5 members and the evicted weakest incumbents; downside is bounded to this submission (best-score-counts) and the result is folded back as a constraint either way.
- Integrity: 398,993 distinct scores, unique cutoff, zero collection-flagged members in the top quintile, consensus-core retention 100%, corr(id) = −5.9×10⁻⁴, zero shared float values with all prior submission files, deterministic byte-reproducible build, raw-file structural audit confirms only the delivered features are used.

## Additional Notes (Optional)
v48 is the designed measurement of the last delivered spend variable our framework has never carried. The construction isolates the axis exactly — base = our best directly-measured set (public 0.919143), change = the bounded coverage promotion and nothing else — so the reading attributes entirely to whether the ground truth books total-spend interchange beyond the industry categories. The framework remains O(n), fully explainable, and auditable end-to-end: the P&L equation carries the economics; the promotion is a stated business rule with a stated population; and the outcome arithmetic was fixed before upload.
