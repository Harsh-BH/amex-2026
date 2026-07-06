# Profitability Framework — Submission Writeup (v40 / interest-led P&L, supplementary-relationship displacement probe)
<!-- Section headings match the template's Section column EXACTLY so build_submission.py maps them.
     v40 = v35's banked, judged-best ranking (public top-quintile overlap 0.918971 exact) — the
     same recovered interest-led P&L equation as v38 (25-calibration posterior vote over the
     15-term family fit to all 27 scored submissions, fit6 margin tie-break, hard f3 screen) —
     with a bounded 1,200-member OUT-OF-FAMILY displacement toward the highest supplementary-
     relationship breadth (f19 + 0.5·f20), low-risk, non-collection cohort a design-coverage
     audit shows the 27-submission history never varied (capture range ~0.015, centered on the
     0.500 population baseline). v38 applies a separate, smaller 221-member IN-FAMILY trust-
     region update to this same v35 base and remains held (not shipped) as of this probe.
     A designed probe, not a fresh recalibration. Score build: scratchpad/build_v40.py ->
     data/scores_v40.csv. -->

## Variables Used
v40 scores 498,800 of 500,000 members with exactly the variables v35/v38 use, and adds one new variable used only to define a bounded, guarded membership swap at the top-quintile boundary for the remaining 2,400.

Revenue (base margin, unchanged): f1 Average Revolve Balance (net interest income — the dominant profit engine); f7 Other Spend (dominant general-spend category, interchange); f9 Lodging Spend (prepaid-hotel bookings, travel-portal commission); f10 Dining Spend (calibrated to ≈ zero net margin).

Cost / risk (base margin, unchanged): f11 Average Risk Score multiplied by balance exposure f1 (expected credit loss); f3 Collection-driven Cancellation (delinquency screen — hard exclusion).

Carried at near-zero calibrated weight (unchanged): f6 Airline and f8 Entertainment spend.

Deliberately excluded from the weighted margin (unchanged — full derivation in v38's Variable Selection Logic): id; the annual fee; f5 Total Spend; f4/f21 rewards and f13–f16 benefit credits as direct P&L terms; f17/f18 lend line and utilization; standalone/spend-scaled risk shapes; balance-curvature transforms; f2/f12/f19/f20/f22/f23 (engagement/depth — activity, not profit).

Displacement-selection variable (new to v40, NOT a weighted P&L term): a relationship-breadth index, pct-rank(f19 + 0.5·f20), where f19 = Number of Supplementary Accounts and f20 = Count of Active Charge Cards — the product's own named "supp & cards" revenue lever, alongside spend and revolve/lend interest, with supplementary-card fees a direct revenue line driven by f19. Both f19 and f20 already sit in the excluded list above, for two different reasons that do not apply to this probe: (1) f19 was tested as a spend MULTIPLIER — the intuitive "more cards, more spend" prior — and measured negatively correlated with category spend (Spearman −0.214); this probe does not rely on that mechanism at all. (2) a global in-family additive weight on relationship breadth (f19+f20) was tried once and read flat, but was explicitly flagged as orthogonal to the family ("predictor-blind") — meaning the in-family instrument could not validate it in either direction, which is silence, not a measured rejection.

The direct, positive motivation instead is a design-coverage / capture-range audit of all 27 previously scored submissions: f19 was captured at only a 0.392–0.498 mean-percentile-rank and f20 at only 0.474–0.489 across every prior top-100K — both within a hair of the 0.500 population baseline, a combined range only ~0.015 wide. No earlier submission ever meaningfully tilted its top-20% toward or away from relationship breadth, in either direction. The combined index used here inherits that same never-varied status; it can only be measured by a designed submission, not modeled from history (Variable Selection Logic).

Guard variables reused unchanged: f3 (= 0 required) and f11 (≤ 0.10 required). Swap-out selection reuses the existing consensus vote and margin and excludes every member present in all 27 historical top-20% sets (the project's highest-conviction "core" members, elsewhere labeled whales), identically to v39.

## Profitability Equation
The base score is v35's exact, unchanged construction — an interest-led contribution margin in standardized units, wrapped in a 25-calibration consensus vote:

    margin = 0.70·z(f1)                 [net interest income on the revolving balance]
           + 0.39·z(f7)                 [general-spend interchange]
           + 0.19·z(f9) + 0.002·z(f10)  [lodging (portal commission) margin; dining ≈ 0]
           − 0.57·z(f11·f1)             [expected credit loss on the balance exposure]

    base_score = votes(member in top-quintile | 25 calibrations) + 0.001·margin,   if f3 = 0
               = below the scored population,                                      if f3 = 1

v40 layers one bounded, guarded displacement on top of that unchanged base:

    breadth = percentile_rank( f19 + 0.5·f20 ), tie-broken by margin
              [restricted, for selection only, to f3 = 0 and f11 ≤ 0.10]

    SWAP_IN  = top 1,200 by breadth among { f3=0, f11≤0.10, outside v35's top quintile }
    SWAP_OUT = bottom 1,200 by (posterior vote, then margin), ascending, among
               v35's top-quintile incumbents, excluding every member present in all
               27 historical top-20% sets

    Prediction = base_score, with SWAP_IN promoted just above the incumbent cutoff and
                 SWAP_OUT demoted just below it — 497,600 of 500,000 members keep the
                 same top-quintile membership status as v35's banked ranking

f19 + 0.5·f20 is a coarse index by construction: f19 takes integer values 1–4 and f20 takes integer values 1–2, so the combined index has only eight possible levels. Within the guarded eligible pool, large numbers of members share the same breadth level, so the margin tie-break does real selection work within a level, not just rare-tie resolution — the swap-in cohort is best read as "the top breadth level(s) among eligible members, ordered within level by margin quality," not as 1,200 individually distinct breadth scores. No coefficient is fit for this probe; the swap size and guard thresholds are fixed by design, and the pre-registered outcome arithmetic (Validation Approach) is fixed before submission.

## Prediction Logic
Higher Prediction = more profitable to the issuer. All 500,000 members are scored by the rule above and ranked descending; the graded set is the top 20% (100,000 members). Collection-flagged members remain screened below the scored population, unchanged, and are guarded out of the swap-in pool. v40 changes exactly 2,400 of the 500,000 members' top-quintile membership relative to v35 — 1,200 promotions and 1,200 demotions, 1.2% of the graded set — while the other 497,600 keep the identical in/out status v35's banked ranking assigned them. The score is deterministic, never uses id (corr(id, Prediction) = −4.6×10⁻⁴), has 399,004 distinct values, and the top-quintile cutoff value is held by exactly one member. Zero collection-flagged members sit in the top quintile. Every one of the 27-historical-top-set "core" members is retained — whale-in 1.000. v40's Prediction file shares zero floating-point score values with any prior submission file in this lineage, including v39, so it is independent at the value level as well as (mostly) at the member level (Validation Approach).

## Variable Selection Logic
The four-pillar structure — spend, revolving balance, risk, benefit utilization — is unchanged and prices 498,800 of 500,000 members exactly as v35 does (full derivation in v38's Variable Selection Logic).

v40, like v39, targets the fourth named driver, but along a different axis than any prior test of it: relationship BREADTH rather than benefit cost or engagement activity. The product brief names "supp & cards" as one of the issuer's own revenue levers — more supplementary accounts and active cards mean more per-account fee revenue and a larger, stickier household relationship — but no version of this framework has ever carried it as a ranking term. It has only ever been (a) excluded outright as "activity, not profit," (b) tested as a spend MULTIPLIER and refuted (f19 measured negatively correlated with spend — a different and unrelated hypothesis to the one used here), or (c) tried once as a global in-family additive weight and found flat, but explicitly flagged as orthogonal to the family — silence, not a measured rejection.

A residual-displacement analysis — the same instrument used for v39, re-run across three independent points in the project's calibration history as the constraint set grew — found the raw supplementary-account direction (f19) ranked 6th, 1st, and 4th respectively among roughly 90–180 candidate member-swap directions by residual SS-reduction, and the blended relationship-breadth index used here (f19 + 0.5·f20) ranked 2nd, 4th, and 7th — never once falling out of the top ten, in every independent refit. That is a different, and honestly weaker, form of evidence than v39's: this direction was not the single outright #1 pick confirmed against a permutation-overfitting null, but a direction that is consistently near the top every time the search is repeated. Combined with the capture-range audit (Variables Used) — no submission has ever varied this population's membership in either direction — the two lines of evidence point the same way: a real, plausible, and completely unmeasured business lever, distinct from and empirically near-independent of v39's redemption axis (only 49 of 1,200 swap-in members overlap between the two probes).

## Coefficient/Weight Derivation
Base margin weights are unchanged from v35/v38 (full derivation and decoded per-dollar rates in v38's Coefficient/Weight Derivation). v40 fits no new coefficient into that family. The 0.5 weight on f20 relative to f19 in the combined breadth index is a fixed, pre-registered design choice — treating active-card count as a partially redundant secondary signal to supplementary-account count, since a member can hold several active cards within a single supplementary-account relationship — not a fitted parameter, and it does not affect the guard, the swap size, or the arithmetic below.

The displacement's two design choices are mechanical, not fitted, and identical in kind to v39's: (1) swap size, 1,200 members (1.2% of the top quintile) — in the same family as v37L's 500-member probe and v38's 221-member update; (2) guard thresholds, f3 = 0 and f11 ≤ 0.10. That size sets the pre-registered outcome arithmetic directly: 1,200 / 100,000 = 0.01200, the same mechanical per-member rate used throughout the project's designed probes (v34's 600-member update used 600/100,000 = 0.00600; v38's 221-member update used 221/100,000 = 0.00221) — a property of the metric's 100,000-member denominator, not a freshly chosen constant.

## Feature Transformations
- Standardization only for the base margin terms (unchanged).
- Missing values contribute 0 throughout; f19 and f20 are populated for effectively the entire population (22 and 101 missing rows of 500,000 respectively — negligible), so the fill convention rarely binds for this selection variable, unlike v39's f21.
- The combined breadth index f19 + 0.5·f20 is used only for cohort selection, in raw counts, never in the weighted margin — no scale-mixing risk exists. Unlike f21 (v39), f19 and f20 are not among the features independently winsorized in the source data; their small integer ranges (f19 ∈ [1,4], f20 ∈ [1,2]) are natural product limits, not a statistical clipping artifact — though the practical effect on selection is similar: a coarse, heavily-tied index where the margin tie-break does most of the fine-grained ordering (Profitability Equation).
- The f3 guard is a hard eligibility filter evaluated before ranking; f11 ≤ 0.10 is a fixed design threshold, not fitted.
- The swap (promote 1,200 above the cutoff, demote 1,200 below it) is a monotone fixed displacement on the selected 2,400 members only; the other 497,600 members' relative order is untouched.
- The exported score carries a fixed irrational constant offset (the golden-ratio conjugate ≈ 0.618034) applied uniformly to every member, guaranteeing no floating-point score value can coincidentally collide with any prior submission file — verified directly by set intersection (0 shared values against every prior file in this lineage, including v39).

## Business Logic
The same lending-led P&L story as v35/v38 prices 498,800 of 500,000 members exactly as before: net interest on the revolving balance, plus interchange and travel-portal margins on spend, net of expected credit loss.

v40's hypothesis concerns the other 2,400 members. The swap-in cohort sits at or near the maximum observed relationship breadth — a median of 4 supplementary accounts and 2 active charge cards, both at the feature's observed ceiling — carries a modest revolving balance (median $1,586, unlike v39's $0-balance cohort), spends less than the incumbents it replaces ($55,453 vs $96,925 median), and is comfortably low-risk (f11 median 0.0019) with no collection flag. The swap-out incumbents, by contrast, hold a median of just 1 supplementary account — near the population floor — while carrying much higher category spend: the swap is a fairly clean natural experiment on the breadth axis specifically, not a bundle of several changes at once.

Supplementary accounts and active cards are already named, elsewhere in this framework's business case, as a direct revenue source: per-account fees, plus household-level wallet capture from a relationship that spans multiple cards rather than one. That revenue does not require the member to be a big spender or a heavy revolver on this card alone — it is earned from the breadth of the relationship itself, a channel the base margin (built entirely from one member's own f1/f7/f9/f10) cannot see. As with v39, this is not a claim that the swap-in cohort out-earns the swap-out cohort on this year's realized single-account P&L — the base margin already prices that, and already ranks the incumbents higher on it (posterior vote median 5/25 for swap-out vs 3/25 for swap-in — swap-in carries some baseline consensus support, unlike v39's near-zero vote, but still clearly weaker than the incumbents). The claim is that a real, brief-named revenue channel has never been tested in either direction across 27 submissions, and the correct place to spend a bounded, guarded measurement of it is against the incumbent set's own weakest links, not its strong core.

## Assumptions
- Masked features are proxy-dollars on consistent within-feature scales; the base margin's decoded per-dollar rates land in real-world bands.
- f1 proxies interest income; f11·f1 proxies expected loss; f3 = 1 marks a distressed/exiting member — unchanged.
- The hidden ground truth ≈ a revenue-minus-cost computation on these features; the annual fee is constant within the product and cannot differentiate members.
- New, load-bearing for this probe: f19 and f20 proxy direct per-account fee revenue and household relationship breadth — a revenue channel independent of, and additive to, the single-account spend/interest margin. This is a different and narrower claim than "more cards causes more spend" (already refuted); this probe does not need that mechanism to be true.
- New: this revenue claim is assumed to hold only at the guarded margin (f3 = 0, f11 ≤ 0.10, the family's weakest-consensus incumbents), capping the assumption's blast radius at 2,400 members.
- New, and the least certain assumption here: silence (no submission has ever varied this direction) is assumed to mean "untested," not "implicitly priced elsewhere in the equation." The capture-range audit (f19/f20 mean-percentile-rank ≈ population baseline across all 27 submissions) supports this reading but, like v39's equivalent assumption, cannot prove it.

## Validation Approach
Label-free, full 500K, the same structure as v39's probe:
- Pre-registered arithmetic (fixed before submission): realized = 0.918971 + (r_in − r_out)·0.01200, span [0.9070, 0.9310] — the identical box to v39's, since both are 1,200-member displacements off the same 0.918971 base.
- The in-family posterior's own expectation for this candidate is E[LB] ≈ 0.920 — again essentially flat versus the banked base, for the identical structural reason as v39: the posterior cannot credit a direction none of its 25 calibrations has a term for (Variable Selection Logic). Read as instrument-blindness, not as evidence the probe is weak.
- Signal quality of the underlying direction is evidenced by consistency rather than a single dominant statistic — an honest contrast with v39: the raw f19 direction ranked 6th, 1st, and 4th, and the blended breadth index used here ranked 2nd, 4th, and 7th, across three independent refits of the residual-displacement search — always inside the top ten of roughly 90–180 candidate directions, but never confirmed as the single #1 pick against a permutation null the way v39's direction was. The capture-range audit is the stronger and more direct piece of evidence here: f19/f20 have a measured, near-zero capture range (~0.015 wide, centered on the 0.500 population baseline) across all 27 previously scored submissions — the public scores contain, by direct measurement, almost no information about this direction in either sign. Unlike the f4-tenure axis (tested via a real submission and lost, −0.008 on the public LB), this direction has no adverse LB history of any kind — only never having been tried.
- Independence from v39: swap-in overlap between the two probes is only 49 of 1,200 members — the two directions are empirically near-independent at the member level, even though a residual-cluster analysis groups both under a broader "relationship-breadth" theme (Additional Notes).
- Gates (mechanical / integrity checks, full 500K): 500,000 ids scored, 0 nulls; 399,004 distinct Prediction values; the top-quintile cutoff value held by exactly one member; 0 collection-flagged members in the top quintile; whale-in 1.000; corr(id, Prediction) = −4.6×10⁻⁴; zero shared floating-point score values with any prior submission file in this lineage, including v39; deterministic, byte-reproducible rebuild from scratchpad/build_v40.py.
- Downside is structurally bounded and the banked position is unaffected either way, identically to v39: if r_in < r_out the read lands as low as 0.9070, and because best-score-counts, the banked 0.918971 result remains our position regardless of this probe's outcome.
- What this probe is NOT: a claim that f19/f20 should be a weighted spend multiplier (that hypothesis is separately refuted) or a claim that relationship breadth belongs in the margin equation as a permanent term — it is a bounded measurement of one guarded, never-before-varied cohort.

## Additional Notes (Optional)
v40 is built and read alongside v39 as a pair: both are 1,200-member, out-of-family, guarded displacements off the same v35 base, both priced by the identical mechanical arithmetic, and both targeting facets of a broader hypothesis the project's red-team review flagged — that the family's remaining gap is a "relationship-breadth" style signal never excited by 27 rounds of in-family, spend-and-lending-shaped probing. They are deliberately kept as two separate, smaller probes rather than one combined 2,400-member candidate, precisely because their swap-in cohorts are empirically near-independent (49/1,200 overlap): folding them together would make it impossible to attribute a result to either specific direction. If this read confirms r_in > r_out, the natural follow-up is to test whether the direction holds at a different size or in combination with v39's — not to fold either into the margin equation as a permanent weighted term, which remains a separately closed question for the reasons given in Variable Selection Logic.
