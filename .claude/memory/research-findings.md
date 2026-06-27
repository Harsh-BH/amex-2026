# Research Findings — Literature Review (R1 framework design)

_Distilled, verified takeaways from the 2026-06-27 academic lit review (arXiv + web, adversarially
verified). Full report + reading list: `reports/literature-review-r1-profitability.md`._
_This is the academic backing for `[[profitability-framework-design]]`. Citations checked: the four
agent-sourced arXiv IDs were confirmed real via `get_paper`; EJOR/DSS papers are DOI-cited (re-verify before the graded writeup). Full source list + read-status: [[bibliography]]._

## The equation skeleton the literature converges on
```
profit_score(member) = [ Revenue − Cost ] × (1 − ExpectedLossRate(risk))
```
equivalently (PCLV / e-Profits form):
```
score = ContributionMargin × Persistence − ExpectedLoss
ContributionMargin = Σ revenue terms − Σ cost terms
Persistence        = a [0,1] engagement/retention proxy
ExpectedLoss       = risk × exposure   (the EMP "LGD × EAD × PD" shape)
```

**Two things the literature settles for us:**
1. **Risk MULTIPLIES, it does not add.** Discount revenue by risk; don't drop risk in as one more weighted term. (RAR — EJOR S0377221712006078; two-stage — arXiv:2009.04536; EMP — EJOR 10.1016/j.ejor.2014.04.001). Rationale: the highest-spend/highest-revolve members are often the highest-risk; additive risk under-corrects them.
2. **Segment first (transactor vs revolver), then score on different revenue formulas.** Revolvers earn interest (dominant); transactors earn thin interchange. (Transactor/Revolver scorecard — DSS 2014, eprints.soton.ac.uk/359696). **Our ~60% missingness on `f17`/`f18` is the natural charge-only/transactor flag** (ties to assumption A4).

## Feature mapping (literature backs the STRUCTURE; the f-code assignments are our business-driven design)
| Component | Features | Role |
|---|---|---|
| Interchange on spend (margin-weight by category) | `f5`–`f10` (`f7` refunds negative) | Revenue |
| Revolving balance → net interest (heavy weight for revolvers) | `f1` | Revenue |
| Lend lines + transactor/revolver flag | `f17`,`f18` | Revenue + segment flag |
| Rewards redeemed = realized cost (full weight) | `f21` | Cost |
| Rewards balance = contingent liability (discount by breakage factor) | `f4` | Cost |
| Benefit credits (consider saturating/piecewise transform) | `f13`–`f16` | Cost |
| Risk score (~PD) → multiplicative discount, scaled by exposure | `f11` | Risk |
| Collections-driven cancel calls (amplify risk discount) | `f3` | Risk |
| Cancellation calls → lower the persistence multiplier | `f2` | Risk/persistence |
| Relationship breadth (fees + stickiness) | `f19`,`f20` | Revenue + persistence |
| Engagement → feeds `[0,1]` persistence term | `f12`,`f22`,`f23` | Persistence |

Separate **healthy revolvers** (high `f1`, low `f11`) from **at-risk revolvers** (high `f1` + high `f11` + `f3`).

## Normalization & weighting
- **Log/winsorize heavy-tailed dollar features** (`f5`,`f4`,`f21`) before combining, else whales swamp the ~0.03-scale `f11` (ZILN — arXiv:1912.07753). Directly addresses CLAUDE.md §17 scale-mixing pitfall.
- **Cap/anchor at business-justified levels**, not empirical extremes, to stabilize the top-20% boundary.
- **Margin-weight each behavior** (don't sum raw values) — CSHURI arXiv:1205.1609.
- The multiplicative `margin × [0,1] persistence` form is itself a normalizer (PCLV arXiv:2506.22711).
- Set weights by business reasoning first; if blending data-driven weights, test rank stability.

## Label-free construction & validation (we have NO target — do not invent one)
- **Construct, don't fit.** Closed-form profit from behavior is a peer-reviewed paradigm (Budd & Taylor arXiv:1506.05376).
- **Internal metric = normalized Gini + decile/top-quintile lift** (ZILN arXiv:1912.07753) — closest computable proxy for the top-20%-overlap metric.
- **Headline evidence = top-quintile lift vs random** (retail-banking CLV showed 3.2× top-decile lift, arXiv:2304.03038).
- **Overfit guard = rank stability**: do the SAME members stay in the top-20% under bootstrap resamples AND weight perturbations? (mirrors public-70/private-30 risk). Feeds `[[evaluation]]` + `[[weight-calibration]]`.
- **Optimize the tail, not the bulk** — value is concentrated (arXiv:2506.11037); ranking ≠ calibration (EMP).
- A single tunable profit-weight knob can lift both precision and profit at the top (arXiv:2203.06641).

## Caveats (also in the report)
- f-code mappings are our extrapolation, not stated in any paper → present as design rationale.
- MCDA/composite-indicator methods (TOPSIS, entropy-weight, OECD handbook) are reasonable but **uncited** in the verified set → source a primary ref before claiming literature support.
- Don't quote macro stats ("~80% profit from revolving", redemption %, Fed per-account figures) as paper findings — directional priors only.
- 2 papers flagged **overstated**: Fairness-in-Credit-Scoring (2103.01907, use only for "profit > accuracy"); Points-Rewards (2506.03911, program-design not balance-scoring).

## Top citations for the graded Framework writeup
1. Multiplicative risk discount — RAR, EJOR S0377221712006078
2. `margin × retention` skeleton — PCLV, arXiv:2506.22711
3. Transactor/revolver segmentation — DSS 2014, eprints.soton.ac.uk/359696
4. Expected loss = exposure × risk — EMP, EJOR 10.1016/j.ejor.2014.04.001
5. Profit-objective + Gini/decile validation — e-Profits arXiv:2507.08860; ZILN arXiv:1912.07753
6. Top-quintile separation evidence (3.2× lift) — arXiv:2304.03038

## Round-2 additions (gap-fill: CLV canon, LTR, MCDA, segmentation, behavioral)
_Full prose: report addendum + [[bibliography]] round 2. These refine, not replace, the skeleton above._

**Treat the framework explicitly as a composite indicator + behavioral scorecard.**
- **Adopt the OECD/JRC 7-step pipeline as the Framework-sheet skeleton:** framework → sign-orient → normalize → weight → aggregate → robustness (Handbook 2008). Highest-value, lowest-risk move for the interpretability grade.
- **Sign-orient first**, then **rank/percentile-transform each feature** (preferred over min-max): neutralizes the `f11`≈0.03 vs `f4`≈126K scale mismatch AND heavy tails in one step, and ranking-into-the-top-quintile *is the operation Amex grades* (RFM lineage: Bult-Wansbeek 1995, Hughes 1994).
- **Objective, label-free weighting:** **CRITIC** primary (correlation-aware → deflates collinear `f5–f10`, `f13–f16`), **Shannon-entropy** baseline, **equal-weight** floor — then tilt by P&L sign. (Diakoulaki 1995; Karagiannis 2020.)
- **Use a partially-compensatory aggregator** (geometric mean / penalized) so high spend can't mask high `f11` risk or heavy `f13–f16` cost; benchmark vs arithmetic. Weights ≠ importance under non-linear aggregation (Greco 2019).
- **Alternative engine — TOPSIS:** rank by closeness `C∈[0,1]` to the ideal-profitable member; interpretable, bounded, scores all 500K (Hwang-Yoon 1981).
- **Reciprocal Rank Fusion (Cormack 2009)** = a label-free, scale-free way to fuse revenue/lend/cost/risk/engagement sub-rankings; use as fusion engine OR robustness benchmark vs the weighted sum.

**Validation (label-free) gets sharper:**
- **Monte-Carlo sensitivity over {normalization × weights × aggregation}** → report **top-20% membership stability** (Saisana 2005). This is THE no-label validation + overfit guard; feeds `[[evaluation]]`.
- **SoftRank** perturbation → expected top-20% membership; **ListNet softmax** → top-k inclusion probability (borderline-member confidence).

**Weighting prior, now quantified:** retention/risk should carry MORE leverage than marginal spend — Gupta-Lehmann-Stuart (2004): 1% retention ≈ 5× a 1% margin change (elasticity 3–7). (Firm-value result → per-member heuristic, not theorem.)

**Cost/risk side refinements:**
- Frame as a **behavioral profit scorecard** (Thomas-Edelman-Crook): additive binned point contributions; encode structured-missing clusters as **their own bins**.
- **Multiplicative risk-AND-retention discount**: default hazard from `f11`/`f1`/`f3` (Stepanova-Thomas) × attrition hazard from `f2`/`f12`/`f22`/`f23`/`f19`/`f20` (Van den Poel-Lariviere), applied as `revenue × survival × retention`.
- **Weight distress by profit-at-stake** (example-dependent cost, Bahnsen 2015): a cancel call (`f2`) from a high-spend, deep-relationship member costs far more → implement as a `revenue × distress-signal` interaction. So-Thomas (2011) MDP licenses the revenue × risk-discount form for credit cards.

**Feature-engineering primitives (single-table ratios — DFS, Kanter 2015):** redemption intensity `f21/f4`, category mix `f6–f10/f5`, benefit-credit burden `(f13+f14+f15+f16)/spend`, engagement `f12/f20`. Cluster (GMM > k-means on skewed spend; John 2023, bank precedent Aliyev 2020) to build an **internal pseudo-ground-truth** and confirm tier means move monotonically.

**Hard limits (carry into the writeup honestly):** the canon legitimizes the STRUCTURE, never our `f`-code→P&L mapping (our defensible assumption). LTR cannot be *trained* (no labels) — never claim "trained a ranker." Don't claim a "provable upper-bound surrogate" for the hidden metric.

## Net-new citations for the graded writeup (round 2)
Berger-Nasr (1998) — equation form · Gupta-Lehmann-Stuart (2004) — retention-weighting prior · Fader-Hardie-Lee (2005, JMR) — label-free RFM→value · OECD/JRC Handbook (2008) — 7-step pipeline · Saisana-Saltelli-Tarantola (2005) — sensitivity validation · Cormack (2009) — Reciprocal Rank Fusion.

## Round-3 additions (premium-card economics, rewards costing, label-free validation)
_Research phase CLOSED after round 3 (diminishing returns). Full prose: report round-3 addendum + [[bibliography]] round 3._

**Missingness-as-signal — now has a primary citation.** MIA (Twala-Jones-Hand 2008, *Pattern Recognition Letters*): encode the structured co-missing clusters as **their own signed terms**, do NOT fill-with-0. Charge-only flag (`f17`/`f18` ~60% missing) gets its own weight. This is the principled answer to CLAUDE.md §17's fill-0 pitfall.

**Aggregation — a citable non-compensatory option.** AMPI (Mazziotta-Pareto 2018, `Compind::ci_ampi`): goalpost-normalize → arithmetic mean → **subtract a CV-based imbalance penalty** so a lopsided member (huge spend, extreme risk) can't fully compensate. **A/B this vs the weighted-sum/geometric baseline** — a balanced profitable member may rank better, improving top-20% precision. Goalpost scaling also cleanly mixes `f11`≈0.03 with `f4`≈126K.

**Premium charge-card physics (the Amex-specific correction):**
- Profit is **interchange-on-spend-dominated**; the lending engine is weaker than a generic revolving card. BUT **top spenders ≠ most profitable** (Fed FEDS Note 2022) → **do NOT use raw `f5` as the top-20% sort key.** Keep a strong net-spend term (net `f7` refunds) AND a revolve/lend term (`f1`/`f17`/`f18`) discounted by risk, with reward cost netted.
- **Segment-aware (piecewise), not one linear revolve coefficient** (So-Thomas-Seow-Mues 2014, DSS): transactors (low/absent `f1`, missing `f17`/`f18`) → net spend × reward-cost efficiency; revolvers/lenders → add risk-discounted interest term.
- **Wallet-capture term** (Du-Kamakura-Mela 2007; Glady-Croux 2009): `f5`–`f10` = size-of-wallet proxy, `f19`/`f20` + category breadth = share-of-wallet proxy. High `f5` ≠ dominant captured share.
- Premium-card reality: points + lifestyle credits consume **60%+ of premium-card revenue** → reward/benefit cost MUST be netted, not ignored.

**Rewards cost — set the `f4` discount precisely:**
- `f21` (redeemed) = realized cost, weight ≈ 1. `f4` (balance) = **contingent** liability: cost ≈ `f4 × p_redeem × cost-per-point` (Gault et al. 2012, CAS; IATA IFRS-15).
- **~17–18% breakage benchmark → ~80–90% redemption-discount band** (sensitivity band, not point estimate).
- **Per-member modulation:** use `f21/f4` (or `f21/(f4+f21)`) redemption ratio + engagement (`f12`,`f22`/`f23`) — dormant high-balance accumulators break (cheaper); engaged redeemers cost near-full. Concave/threshold transform on `f4` (Hssaine 2025). Revenue-contingency: scale `f4` penalty down where spend is high (Chun et al. 2020).
- `f13`–`f16` = **utilization-driven costs** (observed magnitude already reflects usage; low utilization = margin tailwind).

**Label-free validation protocol (4 families) — feeds `[[evaluation]]`:**
1. **Spectral agreement** (Parisi-Nadler SML, PNAS 2014, arXiv:1303.3257; Jaffe 2015): build 3–5 semi-independent sub-scores, leading eigenvector of their agreement-covariance ranks/weights them. *Caveat: shared features → corroboration, not proof.*
2. **Monte-Carlo + Sobol robustness** (Saisana 2005; OECD 2008): randomize normalization/weights/imputation → top-20% membership-stability fraction + sensitivity attribution.
3. **Bootstrap rank-stability** (challengeR, Maier-Hein 2021): resample 500K, recompute top-20%, report retention frequency + Kendall-τ — internal proxy for public-70%→hidden-30%.
4. **Weak-supervision proxy** (Snorkel/Data Programming, Ratner 2016, arXiv:1605.07723): denoise business-rule labeling functions into a soft "high-profit" target — **sanity-check ONLY, never a training target**.
+ **Lorenz/Gini concentration** as an in-house tie-breaker between candidate frameworks (in the spirit of Goix MV/EM 2016).

**Net-new citations (round 3):** Twala MIA (2008) · Mazziotta-Pareto AMPI (2018) · Saisana (2005)+OECD (2008) · Glady-Croux (2009) · Gault CAS (2012)+IATA 17–18% breakage · Parisi SML (2014) · So-Thomas-Seow-Mues (2014).

**Soft numerals to re-source before quoting:** AMPI [70,130] goalpost; Chun "Delta $412M→$2.4B" (drop); IATA per-airline 2024 liability dollars (the 17–18% breakage is firm).
