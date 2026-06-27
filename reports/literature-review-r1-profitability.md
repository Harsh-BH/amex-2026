<!-- Generated 2026-06-27 by the amex-profitability-lit-review workflow (11 agents, arXiv MCP + WebSearch, adversarial verification). -->
<!-- Citation spot-check (main session, arXiv get_paper): 2009.04536, 1703.02596, 1403.6531, 2103.01907 all confirmed real with matching titles. EJOR/DSS papers (RAR S0377221712006078; Transactor/Revolver DSS 2014 eprints.soton.ac.uk/359696; EMP 10.1016/j.ejor.2014.04.001) are DOI-cited, not arXiv — re-verify before quoting in the graded writeup. -->

# Literature Review: Designing an Interpretable Revenue−Cost Profitability Ranking for Amex Premier Cardmembers

*Scope: rank 500,000 Premier charge-card members by profitability to the issuer, with no profitability label, graded on the % overlap between our Top-20% and the true Top-20% (precision @ top quintile, hidden 30% holdout). This report includes only papers whose adversarial verification status was* supported *or* overstated*; overstated papers are flagged inline. Papers marked unverifiable or hallucinated are excluded.*

---

## 1. Executive Summary

- **Adopt the verified CLV identity as the equation skeleton: `value = contribution margin × retention probability − cost`.** This `margin × [0,1] probability − cost` form is the cleanest, best-supported template for us (*Potential Customer Lifetime Value in Financial Institutions*, arXiv:2506.22711; *e-Profits*, arXiv:2507.08860). The multiplicative probability term also normalizes a dollar quantity against a survival/engagement weight with no ad-hoc scaling.

- **Discount revenue by risk multiplicatively, do not add risk as a separate term.** Two-stage credit-then-profit scoring (*Integrating Credit Scoring into Profit Scoring*, arXiv:2009.04536) and Risk-Adjusted Revenue (*RAR*, EJOR S0377221712006078) both support `profit = revenue × (1 − expected_loss(risk)) − cost`. This protects the graded top-20%, because the highest-spend / highest-revolve members tend to also be the highest-risk.

- **Transactor vs. revolver is a verified primary profit axis.** The two segments have fundamentally different economics — revolvers earn interest (dominant), transactors earn thin interchange — and a segment-aware profit model beats one undifferentiated weighted sum (*Transactor/Revolver scorecard*, DSS 2014, eprints.soton.ac.uk/359696). Our ~60% missingness on lend lines (f17/f18) is the natural transactor/charge-only flag.

- **Rewards are a deferred, contingent cost realized mainly on redemption, not accrual.** Treat points *redeemed* (f21) as realized cost at full weight and points *balance* (f4) as a discounted contingent liability (apply a redemption/breakage factor), supported by the redemption-threshold framing in *Learning Fair and Effective Points-Based Rewards Programs* (arXiv:2506.03911). This avoids over-penalizing large accruers who never redeem.

- **Profit can and should be a transparent closed-form function of behavioral primitives — no label required.** Peer-reviewed credit-card profitability is built this way (*Calculating optimal limits for transacting credit card customers*, arXiv:1506.05376), which exactly matches our label-free situation and validates designing an equation over training a black box.

- **A generic accuracy/relevance metric ranks the profitable tail WRONG.** The single most-repeated finding across themes: profit-aware ranking reshuffles who lands at the top vs. AUC/F1/MAP (*e-Profits* 2507.08860; *Customer Price Preference and Product Profit* 2203.06641). Since we are graded *only* on top-20% overlap, we must model the value structure explicitly and validate at the top.

- **Value is extremely concentrated in a rare high-value tail.** A tiny fraction of members drive most issuer profit (*GRePO-LTV*, arXiv:2506.11037, ~0.1% conversion; reinforced by ZILN's heavy tail, arXiv:1912.07753). Engineer the score to separate the rare top tail, not to fit the bulk.

- **Log-transform / winsorize heavy-tailed dollar features before combining.** Raw heavy-tailed money terms (spend f5, rewards f4) mixed with a ~0.03-scale risk feature (f11) would let whales swamp the weighted sum (*ZILN*, arXiv:1912.07753; cap-at-desired-level idea in TOPSIS-RAD, scout-cited).

- **Use normalized Gini + decile / top-quintile lift as the internal label-free validation metric.** ZILN (arXiv:1912.07753) explicitly recommends both; Gini measures how well the score concentrates value at the top — the closest computable analog to the competition's top-20% overlap.

- **Top-decile lift is the proven, label-free way to demonstrate separation.** *Modelling CLV in retail banking* (arXiv:2304.03038, verified) showed top 10% by propensity were **3.2× more likely** to convert than random. We can analogously prove our top quintile concentrates high-revenue behaviors far above random — the template for defending top-20% separation in the writeup.

- **Build the score as a customer-level income statement (component attribution).** Enumerate each behavioral "portfolio component" and attribute a revenue or cost contribution to each (*Bank Business Models, Size, and Profitability*, arXiv:2401.12323 — note: bank-level, supports the attribution *idea* only).

- **Validate label-free via rank stability, not point error.** Resample/perturbation stability of top-quintile membership, weight-sensitivity analysis, and agreement across alternative aggregation rules are the field-standard substitutes for accuracy when there is no ground-truth label.

---

## 2. Per-Theme Synthesis

### Theme A — Customer Profitability & Lifetime Value

**Strongest verified papers and what they contribute:**

- **Potential Customer Lifetime Value in Financial Institutions** — arXiv:2506.22711. Confirms `CLV = Contribution Margin × Retention Probability`, predicting retention probability and Potential Contribution Margins, then multiplying. *Implies:* our cleanest skeleton — `score = (monetized margin) × (retention/engagement proxy) − (expected loss)`. (Caveat: the paper does not name our feature codes; the f-mapping is our extrapolation.)
- **A Deep Probabilistic Model for CLV Prediction (ZILN)** — arXiv:1912.07753. Zero-inflated lognormal: a zero point-mass for "never transacts/revolves" plus a lognormal heavy tail for magnitude; explicitly recommends **normalized Gini** (discrimination) and **decile charts** (calibration). *Implies:* (1) log/winsorize heavy-tailed dollar features; (2) separate "does this member transact/revolve at all" from "how much"; (3) use Gini + decile lift as our label-free validation.
- **Modelling customer lifetime-value in the retail banking industry** — arXiv:2304.03038. Product-based propensity over arbitrary horizons; verified **43% out-of-time error reduction** and the **3.2× top-decile lift**. *Implies:* additive per-revenue-stream structure, and a concrete label-free top-quintile separation template.
- **e-Profits** — arXiv:2507.08860. Per-customer profit = f(CLV, retention probability, intervention cost), using Kaplan-Meier *customer-level* (not population-level) retention; shows profit-based evaluation reshapes model rankings vs AUC/F1. *Implies:* optimize/validate for top-quintile separation; use a per-member, not one-size-fits-all, retention multiplier.
- **Bank Business Models, Size, and Profitability** — arXiv:2401.12323. Decomposes profitability by portfolio component. *Implies:* the component-attribution / customer-income-statement structure. (Bank-level study — supports the attribution idea only, not a per-customer formula.)
- **CSHURI — Customer Segmentation and Transaction Profitability** — arXiv:1205.1609. Margin/utility-weighted association mining; high-margin behaviors count more. *Implies:* margin-weight each behavior rather than summing raw values.
- **CLV Prediction Using Embeddings (ASOS)** — arXiv:1703.02596. Production CLTV; SOTA baseline was hand-crafted features + ensemble, embeddings gave only incremental lift. *Implies:* an interpretable hand-crafted score is a legitimately strong baseline; embeddings are off-limits for us.
- **GRePO-LTV (WeChat)** — arXiv:2506.11037. Graph + Pareto multi-horizon; ~0.1% purchase rate. *Implies:* value is concentrated (engineer for the tail), and multi-task balancing warns not to let one driver (e.g. spend) silently dominate. Method itself too black-box for us.

### Theme B — Credit-Card / Issuer Economics

**Strongest verified papers:**

- **Developing a measure of Risk-Adjusted Revenue (RAR)** — EJOR S0377221712006078 (Singh, Murthi & Steffes, 2013). Customer value = revenue adjusted for risk, because naive CLV overestimates value and revenue & risk are positively correlated. *Implies:* the strongest single risk template — apply f11 (risk/PD) as a **multiplicative discount** on `(revenue − cost)`. (Overstated caveat: the paper uses a CAPM/portfolio risk-adjusted *discount rate*, not a literal `(1 − PD)`; our `(1 − f11_norm)` is a defensible engineering gloss, and "positively correlated" is consistent-but-not-verbatim.)
- **Transactor/Revolver scorecard** — DSS 2014, eprints.soton.ac.uk/359696 (So, Thomas, Seow & Mues). Classifying along the transactor↔revolver spectrum gives more accurate profit estimates than ignoring the split. *Implies:* engineer a transactor/revolver indicator from f1/f17/f18 + missingness; score segments on different revenue formulas (interest-weighted vs interchange-weighted).
- **Calculating optimal limits for transacting credit card customers** — arXiv:1506.05376 (Budd & Taylor). Profit as a closed-form function of a purchase point process; transactor case has no interest revenue, value comes from interchange on spend volume. *Implies:* a separate transactor revenue path; profit as a transparent formula, no label.
- **Weighing Anchor on Credit Card Debt** — arXiv:2305.11375. Non-distressed consumers commonly pay near the minimum, sustaining revolving balances behaviorally. *Implies:* persistent revolving balance (f1) is a durable, defensible revenue stream — but high balance ≠ distress; separate healthy revolvers (high f1, low f11) from at-risk revolvers (high f1, high f11, collections f3).
- **Learning Fair and Effective Points-Based Rewards Programs** — arXiv:2506.03911. A uniform redemption threshold loses at most a `(1 + ln 2)` factor vs full personalization; reward is realized cost only on redemption. *Implies:* treat f21 (redeemed) as realized cost, f4 (balance) as a discounted contingent liability; a single, simply-weighted reward-cost term is defensible (no per-member reward modeling needed). (Overstated caveat: the paper is about program *design*, not scoring an existing points balance.)

> **Unverified macro figures — do NOT cite as from these papers:** "~80% of issuer profit from revolving," "interchange near-zero/negative after rewards," "Fed ~$240 vs ~$25 profit-per-account," "15–30% redemption." These are external/Fed-style claims layered onto the papers; treat as directional priors only, and source a primary Fed/Nilson reference before quoting numbers.

### Theme C — Ranking & Label-Free Composite Scoring

**Strongest verified papers:**

- **Exploring Customer Price Preference and Product Profit Role in Recommender Systems** — arXiv:2203.06641. Re-weights a base ranking by a per-item profit/margin term via a tunable knob; improves **both** precision and realized profit at the top. *Implies:* build a behavioral base score, re-weight by per-member margin proxies, tune the profit-weight while watching top-quintile overlap — profit-weighting and top-k precision are complementary, not in tension.
- **e-Profits** — arXiv:2507.08860 (also Theme A). *Implies:* mirror its `revenue × persistence − (reward + benefit + servicing + expected-loss)` decomposition, with f11 playing the role their retention probability plays.
- **Integrating Credit Scoring into Profit Scoring (P2P)** — arXiv:2009.04536. Two-stage: a risk score conditions the profit model; explicitly argues minimizing risk and maximizing profit are distinct objectives. *Implies:* `profit_score = revenue × (1 − expected_loss(risk)) − cost`, pushing high-spend/high-risk members down.
- **Credit acceptance process strategy case studies** — arXiv:1403.6531 (Przanowski). Three risk models + one propensity model combine into a profitability decision; cutoffs are top-k selection, some profitable, some not; a **5% Gini gain ≈ concrete monthly profit gain**. *Implies:* structure profit as `revenue × acceptance/persistence − loss`; sweep the score and inspect how revenue/cost concentrate near the top-20% boundary.
- **Fairness in Credit Scoring** — arXiv:2103.01907 (Kozodoi, Jacob, Lessmann). *(Status: overstated.)* The paper is real and genuinely profit-oriented (quantifies a profit-fairness trade-off), **but its abstract does not foreground Expected Maximum Profit as a metric.** Use only for the framing "profit is the right objective, accuracy is a poor proxy" — not as a source of an EMP evaluation method. Integrity-relevant: a score must not implicitly proxy a protected/identity attribute (we already forbid `id`).

> **Theme-C verification flag:** the verified paper list contains **zero** papers backing the MCDA / composite-indicator camp (OECD handbook, TOPSIS, entropy-weight, CRITIC, WMSD, TOPSIS-RAD). Those techniques are standard and reasonable, but in this dossier they are **uncited** — do not present them to graders as literature-backed without a primary source.

### Theme D — Credit Risk, Behavioral Scoring & Attrition (cost/risk side)

**Strongest verified paper:**

- **Profit-driven credit scoring with the Expected Maximum Profit (EMP) measure** — EJOR S0377221714003105 (Verbraken, Bravo, Weber, Baesens, 2014; R package `EMP`). Replaces AUC with an expected-profit objective: profit per account = revenue − expected loss = `LGD × EAD × PD`, integrated over a benefit/cost-ratio distribution to yield Expected Maximum Profit and the profit-maximizing cutoff. *Implies:* the canonical scaffold for our cost/risk side — `expected loss = exposure × risk`, i.e. the risk penalty should **scale with each member's own balance/spend exposure** (example-dependent cost), not a flat per-member constant. Reinforces that ranking ability and probability calibration are distinct — for a quintile-overlap metric, optimize separation of the top tail, not global calibration.

*(Other Theme-D items in the dossier were truncated and not independently verified here; the EMP / `LGD×EAD×PD` structure above is the load-bearing, verified contribution.)*

---

## 3. Design Implications for Our Revenue−Cost Framework

### 3.1 Equation structure

The literature converges on one interpretable skeleton, assembled from three verified results:

```
profit_score(member)
  = [ Revenue(member)  −  Cost(member) ]  ×  (1 − ExpectedLossRate(risk))
```

equivalently, in the e-Profits / PCLV form:

```
profit_score(member)
  = ContributionMargin(member) × Persistence(member)  −  ExpectedLoss(member)

ContributionMargin = Σ (revenue terms)  −  Σ (cost terms)
Persistence        = a [0,1] engagement/retention proxy
ExpectedLoss       = risk × exposure   (LGD × EAD × PD form)
```

Backing: PCLV `margin × retention` (arXiv:2506.22711); e-Profits `revenue × retention − cost` (arXiv:2507.08860); EMP `revenue − LGD×EAD×PD` (EJOR S0377221714003105); two-stage risk-discount (arXiv:2009.04536); RAR multiplicative risk adjustment (EJOR S0377221712006078); closed-form-from-behavior, no label (arXiv:1506.05376).

**Two design decisions the literature settles for us:**
1. **Risk multiplies, it does not add.** `× (1 − ExpectedLossRate)` is more defensible than dropping risk into a flat weighted sum (arXiv:2009.04536; EJOR S0377221712006078).
2. **Segment first (transactor vs revolver), then score.** Use different revenue formulas per segment rather than one undifferentiated sum (DSS 2014).

### 3.2 Revenue vs cost vs risk mapping (to our actual features)

> The literature backs the *structure* (revenue−cost−risk; margin-weighting; risk-discount). The specific feature assignments below are **our business-driven mapping**, not stated in any paper — present them as design rationale, not as literature findings.

| Component | Features | Role | Literature backing for the treatment |
|---|---|---|---|
| Interchange on spend (by category) | f5–f10 (f7 refunds can be negative) | **Revenue** — thin margin, net of rewards; margin-weight per category | CSHURI margin-weighting (1205.1609); transactor revenue = interchange (1506.05376, DSS 2014) |
| Revolving balance | f1 | **Revenue** — net interest, the heavy-weight term for revolvers | Durable behavioral revenue (2305.11375); transactor/revolver axis (DSS 2014) |
| Lend lines (total / consumer) | f17, f18 | **Revenue** + **segment flag** — ~60% missing = charge-only/transactor | Transactor/revolver scorecard (DSS 2014) |
| Rewards redeemed | f21 | **Cost** — realized, full weight | Redemption = realized cost (2506.03911) |
| Rewards balance (points outstanding) | f4 | **Cost** — contingent liability, discount by redemption/breakage factor | Deferred/contingent-on-redemption (2506.03911) |
| Benefit credits (lounge, airline, cab, entertainment) | f13–f16 | **Cost** — near-certain fixed cost; consider saturating/piecewise transform (heavy travelers offset, light users pure cost) | Non-linear/threshold reward value (loyalty-design literature, scout-cited) |
| Risk score (~PD) | f11 | **Risk** — multiplicative discount, scaled by exposure | RAR (EJOR S0377221712006078); EMP `LGD×EAD×PD` (S0377221714003105); two-stage (2009.04536) |
| Collections-driven cancellation calls | f3 | **Risk** — near-direct delinquency/attrition flag; amplifies the risk discount | EMP cost/loss side (S0377221714003105) |
| Cancellation calls (attrition) | f2 | **Risk/persistence** — lowers the persistence multiplier | e-Profits retention term (2507.08860) |
| Relationship breadth (supp accounts / active cards) | f19, f20 | **Revenue + persistence** — fee-bearing breadth and stickiness | Component attribution (2401.12323); persistence factor (2507.08860) |
| Engagement (logins, emails opened/clicked) | f12, f22, f23 | **Persistence multiplier** — feeds the `[0,1]` engagement/retention term | PCLV retention proxy (2506.22711); e-Profits (2507.08860) |

**Distinguish revenue-generating revolvers from at-risk revolvers:** high f1 + low f11 = profitable; high f1 + high f11 + high f3 = the risk discount must pull them down (2305.11375 + risk-discount papers).

### 3.3 Label-free construction & validation

There is no profitability label; do **not** invent a target to "train" on. The verified playbook:

- **Construct, don't fit.** Profit as a transparent closed-form function of behavioral primitives is a peer-reviewed paradigm (arXiv:1506.05376), not a workaround.
- **Internal discrimination metric: normalized Gini + decile/top-quintile lift** (ZILN, arXiv:1912.07753). Gini ≈ how well the score concentrates value at the top — the closest computable proxy for the competition metric.
- **Top-decile lift as the headline evidence** (arXiv:2304.03038, verified 3.2×): show our top quintile concentrates high-revenue behaviors far above random.
- **Rank stability as the overfitting guard:** check whether the **same** members stay in the top-20% under (a) bootstrap resamples and (b) reasonable weight perturbations. Robustness of the ordering — not accuracy — is the evidence we can show with no label.
- **Cutoff-sweep diagnostic** (arXiv:1403.6531): sweep the score and inspect how revenue and cost concentrate near the 20% boundary, confirming the equation separates the tail cleanly.
- **Segment sanity checks:** high-monetary, low-risk members must land in the top-20%; if a segment lands where business logic forbids, the weights are wrong.
- **Evaluate by profit/top-segment ROI, not statistical accuracy** (e-Profits, arXiv:2507.08860): the choice of metric reshapes which scoring rule wins — justifying calibrating to top-quintile separation, not correlation/error.

### 3.4 Normalization & weighting of heterogeneous drivers

- **Log-transform or winsorize heavy-tailed dollar features** (spend f5, rewards f4) before combining, so a handful of whales do not swamp a ~0.03-scale risk feature (ZILN, arXiv:1912.07753).
- **Cap/anchor at business-justified "desired" levels** rather than empirical extremes, to stabilize normalization and the top-20% boundary (TOPSIS-RAD veto/cap idea, scout-cited — uncited in the verified set, use as engineering rationale).
- **Margin-weight each behavior**, don't sum raw values: interchange-bearing categories weighted by relative interchange/margin, revolving balance by net interest margin, rewards/benefit usage by their cost rate (CSHURI, arXiv:1205.1609).
- **The multiplicative `margin × [0,1] persistence` form is itself a normalizer** — it scales a dollar quantity against a probability without an ad-hoc scheme (PCLV, arXiv:2506.22711).
- **Balance the drivers so no single term silently dominates** unless business logic justifies it (GRePO multi-task caution, arXiv:2506.11037). Set weights by business reasoning first; if blending data-driven weights (dispersion/conflict), test rank stability before trusting them.

### 3.5 Top-k / ranking evaluation (precision @ 20%)

- **Optimize the tail, not the bulk.** Value is concentrated (arXiv:2506.11037, arXiv:1912.07753); calibration of the middle is irrelevant to a quintile-overlap metric. Ranking ability ≠ calibration (EMP, S0377221714003105).
- **Cutoff selection is inherently tail-sensitive** (arXiv:1403.6531): focus all calibration on the 20% line.
- **A single tunable profit-weight knob lifts both precision and profit at the top** (arXiv:2203.06641) — a low-risk lever, monitored by top-quintile overlap.
- **Internal proxy for the grading metric:** normalized Gini + top-quintile lift + top-20% membership stability under resampling and weight perturbation. This is the defensible substitute when the true top-20% is hidden — and it doubles as the overfitting guard before spending any of the ≤10 submissions.

---

## 4. Ready-to-Cite for the Profitability Framework Writeup

1. **Risk-adjusted ranking (multiplicative risk discount):** "We discount each member's contribution margin by their risk rather than penalizing additively, following Risk-Adjusted Revenue, which shows that ignoring risk overestimates the value of exactly the highest-revenue customers." — *Developing a measure of risk adjusted revenue in the credit cards market*, EJOR S0377221712006078.
2. **Margin × retention skeleton:** "Our score follows the established Potential CLV decomposition, `Contribution Margin × Retention Probability`, instantiating retention from engagement signals." — *Potential Customer Lifetime Value in Financial Institutions*, arXiv:2506.22711.
3. **Transactor/revolver segmentation:** "We score transactors and revolvers on different revenue formulas because the two segments have fundamentally different profit dynamics; a segment-aware profit model is more accurate than one undifferentiated sum." — *Using a Transactor/Revolver scorecard*, DSS 2014, eprints.soton.ac.uk/359696.
4. **Expected-loss cost term scaled by exposure:** "The risk penalty scales with each member's own exposure (`LGD × EAD × PD`), per the Expected Maximum Profit framework for profit-driven credit scoring." — *Profit-driven credit scoring with the EMP measure*, EJOR S0377221714003105.
5. **Profit objective over accuracy + label-free validation:** "Because the grading metric is top-quintile profit overlap, we evaluate by top-segment separation, not statistical accuracy — a profit-aligned evaluation reshuffles which scoring rule wins — and we measure discrimination via normalized Gini and decile lift." — *e-Profits*, arXiv:2507.08860; *A Deep Probabilistic Model for CLV (ZILN)*, arXiv:1912.07753.
6. **Top-quintile separation evidence:** "We demonstrate separation the way label-free CLV work does — our top quintile concentrates high-revenue behavior far above random, mirroring the 3.2× top-decile lift reported for propensity-ranked banking customers." — *Modelling customer lifetime-value in the retail banking industry*, arXiv:2304.03038.

---

## 5. Curated Reading List

**Theme A — Customer Profitability & Lifetime Value**
- *Potential Customer Lifetime Value in Financial Institutions* — arXiv:2506.22711 — the cleanest `margin × retention` skeleton for our score.
- *A Deep Probabilistic Model for CLV Prediction (ZILN)* — arXiv:1912.07753 — log/winsorize heavy tails; use Gini + decile lift as label-free validation.
- *Modelling customer lifetime-value in the retail banking industry* — arXiv:2304.03038 — verified 3.2× top-decile lift, the separation-evidence template.
- *e-Profits* — arXiv:2507.08860 — per-customer `revenue × retention − cost`; profit evaluation reshapes rankings.
- *Bank Business Models, Size, and Profitability* — arXiv:2401.12323 — component-attribution / income-statement structure (bank-level; idea only).
- *CSHURI — Customer Segmentation and Transaction Profitability* — arXiv:1205.1609 — margin-weight each behavior, don't sum raw values.
- *CLV Prediction Using Embeddings (ASOS)* — arXiv:1703.02596 — hand-crafted interpretable features are a strong baseline; embeddings off-limits.
- *GRePO-LTV (WeChat)* — arXiv:2506.11037 — value is concentrated; balance drivers so none dominates.

**Theme B — Credit-Card / Issuer Economics**
- *Developing a measure of Risk-Adjusted Revenue (RAR)* — EJOR S0377221712006078 — multiplicative risk discount on revenue.
- *Using a Transactor/Revolver scorecard* — DSS 2014, eprints.soton.ac.uk/359696 — segment-aware revenue formulas.
- *Calculating optimal limits for transacting credit card customers* — arXiv:1506.05376 — profit as a closed-form, label-free function of behavior.
- *Weighing Anchor on Credit Card Debt* — arXiv:2305.11375 — revolving balance is durable revenue; high balance ≠ distress.
- *Learning Fair and Effective Points-Based Rewards Programs* — arXiv:2506.03911 — reward is realized cost on redemption; a uniform reward-cost term is defensible *(overstated: program-design, not balance-scoring)*.

**Theme C — Ranking & Label-Free Composite Scoring**
- *Exploring Customer Price Preference and Product Profit Role in Recommender Systems* — arXiv:2203.06641 — a tunable profit-weight knob lifts both precision and profit at the top.
- *Integrating Credit Scoring into Profit Scoring (P2P)* — arXiv:2009.04536 — two-stage risk-discounted revenue beats single-objective ranking.
- *Credit acceptance process strategy case studies* — arXiv:1403.6531 — cutoffs are tail-sensitive top-k selection; Gini gains map to profit.
- *Fairness in Credit Scoring* — arXiv:2103.01907 — *(overstated)* use only for "profit > accuracy as the objective," not as an EMP-metric source.

**Theme D — Credit Risk, Behavioral Scoring & Attrition**
- *Profit-driven credit scoring with the Expected Maximum Profit (EMP) measure* — EJOR S0377221714003105 — `expected loss = LGD × EAD × PD`; example-dependent cost; ranking ≠ calibration.

---

## 6. Caveats & Gaps

- **No paper provides a customer-profit *label* — and none should make us invent one.** Every CLV/churn/profit-scoring paper that "trains" (ZILN, e-Profits, Cowan, GRePO, Chamberlain, the P2P and credit-scoring papers) genuinely *has* a value/default/churn label. Their value to us is in **structure and evaluation**, not a transferable training recipe. Do not mistake any of them as license to fabricate an Amex target (a §17 pitfall).
- **All feature-code mappings (f1–f23) are our extrapolation.** No paper states them. Present them as business-driven design rationale, defensible but not literature-backed.
- **The MCDA / composite-indicator camp is uncited in the verified set.** TOPSIS, entropy-weight, CRITIC, WMSD, TOPSIS-RAD, and the OECD handbook are reasonable and standard for label-free weighting/normalization, but **no verified paper here backs them**. If we use these methods, source them with a primary reference before claiming literature support to graders.
- **Unverified macro statistics must not be quoted as paper findings.** "~80% of profit from revolving," "interchange negative after rewards," "Fed $240 vs $25 per account," "15–30% redemption" are external/Fed-style figures layered on the papers, not verified from them. Use as directional priors only; cite a primary Fed/Nilson source if quoting.
- **Two overstated papers, scoped:** *Fairness in Credit Scoring* (arXiv:2103.01907) is real and profit-oriented but does **not** foreground EMP as a metric — use only for the "profit beats accuracy" framing. *Learning Fair and Effective Points-Based Rewards Programs* (arXiv:2506.03911) is about program design/online learning, not scoring a points balance — its "reward = cost on redemption" insight is transplanted, not a direct result.
- **RAR's mechanism is a risk-adjusted discount rate, not literally `(1 − PD)`.** Our `× (1 − f11_norm)` operationalization is a defensible engineering gloss; do not present it as a verbatim formula from the paper. The "revenue and risk are positively correlated" claim is consistent with RAR's motivation but was not verified verbatim.
- **What the literature does NOT settle for us:** the exact functional form of the benefit-credit cost (linear vs saturating/piecewise), the redemption/breakage factor to apply to f4, the precise per-category interchange margins, and the relative weights across revenue streams. These are calibration choices for us to set by business reasoning and stability-test — the literature gives the *shape* of the equation, not its coefficients.


---
---

<!-- ADDENDUM appended 2026-06-27 from gap-fill workflow w47np0wme (11 agents). Spot-checked: arXiv 2008.08662, 2402.04103 confirmed via get_paper; Gupta-Lehmann-Stuart 2004 retention-vs-margin sensitivity confirmed via WebSearch (5% vs 1% firm-value, elasticity 3-7). Journal DOIs not independently re-fetched — re-verify before the graded sheet. -->

# Literature Review Addendum — Gap-Fill (Themes F–J)
### Amex Premier Profitability Framework (Round 1)

> This addendum supplements the prior (arXiv-centric) review, which covered CLV / credit-card-economics / risk-discounting. It adds the five foundations that report lacked: **(F) CLV / customer-equity canon, (G) Learning-to-Rank & top-k metric optimization, (H) composite indicators & MCDA, (I) segmentation & financial feature engineering, (J) behavioral scoring & attrition.** Theme I (segmentation) was dropped from an earlier round; it is restored here in full. Only works verified **supported** or **overstated** are included; **unverifiable** items (Liu 2009 LTR survey, LambdaLoss/Wang 2018, the Precision@k textbook definition, Pfeifer-Carraway 2000, Venkatesan-Kumar 2004, the Mazziotta-Pareto primary source) are explicitly excluded from citations and listed under §6. One author mis-attribution (arXiv:1707.01166) was flagged and that work is **dropped** from citation.

---

## 1. What this addendum adds

- **The marketing-science / OR CLV canon** the arXiv-only report missed — the exact, *label-free* revenue−cost−retention equation skeletons (Berger-Nasr 1998; Gupta-Lehmann-Stuart 2004; Fader-Hardie-Lee iso-value 2005) that an Amex grader will recognize as legitimate.
- **A quantitative weighting prior we can defend without a label**: Gupta-Lehmann-Stuart's sensitivity result (a 1% retention gain moves value ~5× a 1% margin gain, ~50× discount rate) → give the risk/retention multiplier high leverage relative to raw-spend deltas.
- **A named, standard MCDA pipeline** (OECD/JRC Handbook 2008) and three *objective, label-free* weighting methods now in scope: **Shannon-entropy**, **CRITIC** (correlation-aware — ideal for our collinear `f5–f10`), and **TOPSIS** (rank by closeness to the ideal-profitable profile).
- **The correct validation discipline for a no-label score**: Monte-Carlo uncertainty/sensitivity analysis over normalization+weight+aggregation choices (Saisana-Saltelli-Tarantola 2005) — measuring **top-quintile stability**, which maps directly onto our hidden-30% grading.
- **A precise read on Learning-to-Rank**: the *training* canon (RankNet, ListNet, LambdaMART) needs relevance labels and is **inapplicable as a trainer**; what transfers is the **evaluation framing** (our metric = Precision@quintile, set-overlap, order-insensitive in the top) and **label-free rank fusion** (Reciprocal Rank Fusion, Cormack 2009) to combine our P&L sub-rankings.
- **A restored segmentation/feature toolkit**: RFM as a label-free ranking spine (Bult-Wansbeek 1995; Hughes), GMM-over-k-means for heavy-tailed spend (John et al. 2023; bank precedent Aliyev et al. 2020), and DFS ratio primitives (Kanter-Veeramachaneni 2015) for margin/intensity proxies.
- **The load-bearing missingness insight**: treat the structured co-missing clusters (`f6–f10`, `f17/f18`, `f4/f21`) as *informative* binary/category features, not something to impute away (behavioral-scorecard WOE binning; Stepanova-Thomas survival coarse-classification).
- **A profit-aware cost/risk side**: behavioral scoring (Thomas-Edelman-Crook), survival/hazard discounts (Stepanova-Thomas 2002; Van den Poel-Lariviere 2004), example-dependent costs (Bahnsen 2015), and a credit-card profit MDP (So-Thomas 2011) → use a **multiplicative risk-and-retention discount weighted by profit-at-stake**, not a flat dollar subtraction.

---

## 2. Per-theme findings (F–J)

### F. CLV / Customer-Equity Canon

The foundational, heavily-cited customer-value models from marketing science and OR. Several are **label-free** — they fit value from observed behavioral histories (recency/frequency/monetary, margin, retention proxies), not a supervised target — which is exactly our constraint. We borrow their *structure* (discounted margin net of cost × survival; RFM skeleton; iso-value monotonicity; customer equity = Σ CLV) as the justification scaffold, **not** as a literal estimator: we have a single 12-month cross-section (no transaction timestamps) and are graded on top-20% overlap.

**Strongest verified works + contribution + implication:**

- **RFM and CLV: Using Iso-Value Curves for Customer Base Analysis** — Fader, Hardie & Lee (2005) — *JMR* 42(4):415–430, DOI 10.1509/jmkr.2005.42.4.415 (PDF: brucehardie.com/papers/rfm_clv_2005-02-16.pdf). **Contributes:** a Pareto/NBD (transaction flow) + Gamma-Gamma (spend-per-transaction) model that maps any R/F/M triple to expected discounted CLV, plus iso-value curves (many-to-one loci of equal future value). **Implication:** the single strongest citation for our task — it formally links observable behavioral summaries to value *without a label*, and licenses a monotone, many-to-one scoring rule (two different histories → same score). Its **non-linearity warning is directly actionable**: do not sum raw features; log/rank-transform and allow a frequency×monetary interaction to protect top-20% overlap. *(Overstated caveat from Theme I: the claim that iso-value logic "proves value is multiplicative" and therefore favors multiplicative combination is an interpretive leap — use as motivation, not proof.)*

- **Valuing Customers** — Gupta, Lehmann & Stuart (2004) — *JMR* 41(1):7–18, DOI 10.1509/jmkr.41.1.7.25084. **Contributes:** simplified CLV ≈ margin × [r / (1 + d − r)] and a verified sensitivity ranking of drivers (1% retention ≈ 5× a 1% margin change, ≈ 50× discount-rate change; retention elasticity ~3–7). **Implication:** a defensible, label-free weighting prior — give the survival/risk multiplier (`f11`, `f3`, `f2`) high leverage relative to small raw-spend differences. *Caveat:* these are firm-VALUE elasticities on 5 public firms; "retention dominates margin" transfers to per-member top-20% ranking as a **heuristic**, not a theorem.

- **Customer Lifetime Value: Marketing Models and Applications** — Berger & Nasr (1998) — *J. of Interactive Marketing* 12(1):17–30, DOI 10.1002/(SICI)1520-6653(199824)12:1<17::AID-DIR3>3.0.CO;2-K. **Contributes:** the canonical deterministic CLV taxonomy, CLV = Σ_t (revenue_t − cost_t) × retention^t / (1+d)^t. **Implication:** the literal revenue-minus-cost-times-survival template for the Framework writeup, with `f11/f3/f2` standing in for (1−retention)/loss probability. *Caveat:* a structural template — it does **not** validate our specific feature-to-term mapping.

- **Counting Your Customers: Who Are They and What Will They Do Next?** — Schmittlein, Morrison & Colombo (1987) — *Management Science* 33(1):1–24, DOI 10.1287/mnsc.33.1.1. **Contributes:** the seminal Pareto/NBD model; infers P(active) and expected future transactions from recency/frequency alone — fully label-free. **Implication:** academic legitimacy for treating sustained activity/engagement as a forward value signal and down-weighting near-inactive members (low `f5–f10`, high `f2`) as latent dropout. We cite it; we cannot fit it (no timestamps).

- **"Counting Your Customers" the Easy Way (BG/NBD)** — Fader, Hardie & Lee (2005) — *Marketing Science* 24(2):275–284, DOI 10.1287/mksc.1040.0098 (PDF: brucehardie.com/papers/018/...). **Contributes:** the tractable Beta-Geometric/NBD frequency process. **Implication:** supports splitting "how often/how engaged" from "how much per unit" and a multiplicative (not purely additive) revenue sub-score. *Caveat:* the frequency-vs-monetary **decomposition requires BG/NBD + Gamma-Gamma**, not BG/NBD alone — credit accordingly.

- **Return on Marketing: Using Customer Equity to Focus Marketing Strategy** — Rust, Lemon & Zeithaml (2004) — *J. of Marketing* 68(1):109–127, DOI 10.1509/jmkg.68.1.109.24030. **Contributes:** customer equity = Σ CLV; a driver model (value / brand / relationship equity). **Implication:** aggregation logic for a portfolio view, and vocabulary to justify a **relationship-equity term** (benefit usage `f13–f16`, logins `f12`, supplementary `f19`) as value beyond raw spend — presented as analogy, not derived result.

### G. Learning to Rank & Top-k Metric Optimization

LTR fits a scoring function so its induced ordering matches **labeled** relevance grades (pointwise / pairwise / listwise). **The critical finding: every LTR *trainer* requires relevance labels. We have none, so RankNet/LambdaMART/ListNet cannot be run.** What transfers is (a) the **evaluation half** — our metric is Precision@k at k=quintile, a set-overlap score that ignores intra-top-k order, so we optimize *who is in the bucket* around the 80th-percentile boundary, not fine ordering; and (b) the **label-free consensus half** — unsupervised rank fusion to combine our heterogeneous P&L sub-scores.

**Strongest verified works + contribution + implication:**

- **Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods** — Cormack, Clarke & Büttcher (2009) — SIGIR 2009, pp. 758–759, DOI 10.1145/1571941.1572114. **Contributes:** RRFscore(d) = Σ_r 1/(k + rank_r(d)), k≈60 — rank-based (scale-free), top-weighted, robust to a single bad ranker, beats trained rankers on LETOR with no labels. **Implication:** the single most directly droppable mechanism for us — fuse revenue / lend / cost / risk / engagement sub-rankings **without labels**, sidestepping the `f11≈0.03` vs `f4≈126K` normalization headache, and top-heavy by construction (aligns with the metric). Strong candidate as the main fusion engine or a robustness benchmark against a weighted sum.

- **SoftRank: Optimising Non-Smooth Rank Metrics** — Taylor, Guiver, Robertson & Minka (2008) — WSDM 2008, pp. 77–86, DOI 10.1145/1341531.1341544. **Contributes:** smooth each score into a Gaussian → induces a per-item rank *distribution* → optimize the expected metric. **Implication:** the rigorous reason top-k metrics are hard (the sort is non-smooth; our cutoff is a hard threshold) and the **right stability test**: perturb features/weights, re-rank, measure **expected top-20% membership**. Members near the cutoff are where the metric is won or lost — run this before spending a submission.

- **From RankNet to LambdaRank to LambdaMART: An Overview** — Burges (2010) — MSR-TR-2010-82. **Contributes:** the "lambda trick" — weight each pairwise update by |ΔNDCG| of swapping items. **Implication:** the transferable *idea* is "errors near the TOP matter far more." Calibrate/validate weights to maximize separation **around the 80th-percentile cutoff**, not global rank correlation. (Algorithm needs labels to compute ΔNDCG — borrow the principle, not the trainer.)

- **Learning to Rank using Gradient Descent (RankNet)** — Burges et al. (2005) — ICML 2005, pp. 89–96, DOI 10.1145/1102351.1102363. **Contributes:** pairwise loss P(i>j)=σ(s_i−s_j) against a target preference. **Implication:** conceptual only — it legitimizes ranking by a monotone score sorted descending; reusable *if* we ever generate self-supervised pairwise constraints ("strictly more spend AND less risk AND lower cost ⇒ ranks higher"). Needs a target per pair → not a trainer for us.

- **Learning to Rank: From Pairwise to Listwise (ListNet)** — Cao, Qin, Liu, Tsai & Li (2007) — ICML 2007, pp. 129–136, MSR-TR-2007-40, DOI 10.1145/1273496.1273513. **Contributes:** Plackett-Luce top-one probability, softmax over scores exp(s_i)/Σexp(s_j). **Implication:** a clean way to convert raw scores into **top-k inclusion probabilities** — a confidence/stability diagnostic ("how firmly is this member in the top 20%?"). The listwise *loss* needs ground-truth ordering → unusable.

> **Integrity caveat for the writeup (from FLAGS):** do not frame our hand-built equation as a "provable surrogate that upper-bounds" the hidden metric — that LambdaLoss-style guarantee holds only for specific label-driven losses. Use "a well-chosen monotone proxy is the principled response to a non-differentiable top-k target" as *rhetorical* framing, never a mathematical claim. And we did **not** train a ranker — say so plainly; any "trained a ranker" claim would be false and gaming-adjacent.

### H. Composite Indicators & MCDA (weighting / normalization primary sources)

Our profitability framework **is** a composite indicator: many heterogeneous, differently-scaled, label-free drivers collapsed into one ranking. The MCDA literature is the decades-old, citable playbook, and its pipeline maps 1:1: (1) framework → (2) normalize → (3) weight → (4) aggregate → (5) robustness.

**Strongest verified works + contribution + implication:**

- **Handbook on Constructing Composite Indicators: Methodology and User Guide** — Nardo, Saisana, Saltelli, Tarantola, Hoffmann & Giovannini (2008) — OECD/JRC, JRC47008, ISBN 978-92-64-04345-9. **Contributes:** the canonical 7-step pipeline and a menu with formulas — normalization (min-max (x−min)/(max−min); z-score; rank; distance-to-reference), weighting (equal, PCA/factor, budget allocation, AHP, DEA), aggregation (linear/arithmetic = compensatory vs geometric = partial compensation) and a compensability discussion. **Implication:** adopt the 7-step structure **verbatim** as the Framework-sheet skeleton — the single highest-value, lowest-risk move for the interpretability grade. Min-max (or rank) normalize each of `f1–f23` *after sign-orienting* cost/risk features, justify weighting via an objective method, then aggregate.

- **On the Methodological Framework of Composite Indices** — Greco, Ishizaka, Tasiou & Torrisi (2019) — *Social Indicators Research* 141(1):61–94, DOI 10.1007/s11205-017-1832-9. **Contributes:** the modern survey of weighting + aggregation + robustness; subjective vs objective weighting; compensatory vs non-compensatory aggregation; and the warning that **weights are NOT importance coefficients under non-linear aggregation**. **Implication:** justifies choosing an objective weighting method (no label to fit subjective weights) and a **partially-compensatory aggregator** so a whale's spend cannot mask high credit-loss risk (`f11`) or heavy benefit-credit cost (`f13–f16`).

- **Determining objective weights: the CRITIC method** — Diakoulaki, Mavrotas & Papayannakis (1995) — *Computers & Operations Research* 22(7):763–770, DOI 10.1016/0305-0548(94)00059-H. **Contributes:** w_j ∝ σ_j · Σ_k(1 − r_jk) — weight grows with contrast AND with being uncorrelated with others. **Implication:** the **best objective weighting for our correlated clusters** — it deflates the collinear spend cluster (`f6–f10`) for redundancy while preserving independent signals like risk `f11` and attrition calls `f2`. Run as the primary candidate vs entropy and equal-weight baselines.

- **Constructing composite indicators with Shannon entropy** — R. Karagiannis & G. Karagiannis (2020) — *Socio-Economic Planning Sciences* 70:100701, DOI 10.1016/j.seps.2019.03.007. **Contributes:** entropy-weight procedure (weight ∝ dispersion/information content), a worked label-free composite (HDI). **Implication:** a default objective baseline — features that best discriminate members earn weight; then tilt by P&L sign. *Caveat:* the exact entropy formula is the standard textbook form, broadly correct as a representation; re-derive when implementing.

- **Multiple Attribute Decision Making: Methods and Applications (TOPSIS)** — Hwang & Yoon (1981) — Springer LNEMS Vol. 186, DOI 10.1007/978-3-642-48318-9. **Contributes:** the 6-step TOPSIS, closeness C_i = d⁻_i/(d⁺_i + d⁻_i) ∈ [0,1] to ideal-best / anti-ideal profiles. **Implication:** an interpretable alternative scoring engine — define the ideal-profitable Premier member (high spend/revolve, low risk/calls/benefit-cost) and rank everyone by C_i ("% of the way to the ideal member"). Bounded, scores all 500K, pairs naturally with CRITIC/entropy weights, and is a clean comparison against a weighted sum in sensitivity analysis.

- **Uncertainty and sensitivity analysis ... for composite indicators** — Saisana, Saltelli & Tarantola (2005) — *JRSS-A* 168(2):307–323, DOI 10.1111/j.1467-985X.2005.00350.x. **Contributes:** a Monte-Carlo framework — put distributions over discretionary choices (normalization, weights, aggregation), simulate thousands of indices, report each unit's rank distribution, attribute volatility via variance-based (Sobol) sensitivity. **Implication:** **this is our validation substitute for a label** — perturb the normalization+weighting+aggregation and measure stability of the top-20% membership set; a defensible submission's top quintile barely moves. Report this as evidence of robustness and non-gaming.

> *Caveats:* "audit-proof" overstates it — citing MCDA makes choices **defensible/standard**, not **correct**; without a label we can only report stability, never accuracy. If Mazziotta-Pareto (MPI/AMPI) is cited for partial compensation, add and verify its own primary source — none was verified this round.

### I. Customer Segmentation & Financial Feature Engineering *(restored Theme E)*

The toolkit that turns 23 masked features into a defensible ranking with no label, across four pillars: (1) RFM as a label-free spine; (2) value-segmentation via clustering for internal pseudo-ground-truth; (3) transaction feature-engineering primitives; (4) **informative missingness**.

**Strongest verified works + contribution + implication:**

- **RFM origin: Strategic Database Marketing (5×5×5 quintile model)** — Hughes (1994) — McGraw-Hill, ISBN 0071456805; **with the first peer-reviewed RFM formalization**: Bult & Wansbeek (1995), *Marketing Science* 14(4):378–394, DOI 10.1287/mksc.14.4.378. **Contributes:** independent quintile sorts on R/F/M → 125 cells, ranked by value, no fitted label. **Implication:** build the profitability spine as a **quintile/percentile-rank composite, not a regression** — rank-transforming each driver auto-normalizes the `f11≈0.03` vs `f4≈126K` scale mismatch, and ranking into the top quintile *is literally the operation Amex grades*.

- **RFM and CLV: Iso-Value Curves** — Fader, Hardie & Lee (2005) — *JMR* 42(4):415–430, DOI 10.1509/jmkr.2005.42.4.415. *(Cross-listed with Theme F.)* **Contributes:** RFM-type aggregates are (near-)sufficient statistics for forward value. **Implication:** the rigorous defense for ranking on behavioral summaries instead of training a model. Separate a frequency/engagement factor (`f12`, `f20`, `f19`) from a monetary factor (`f5–f10`, `f1`). *(Overstated caveat: "value is multiplicative ⇒ multiplicative combination" is motivation, not a paper result.)*

- **Weighted/extended-RFM (WRFM/eRFM)** — representative: *Procedia Computer Science* 3 (2011), "Estimating CLV Based on RFM Analysis," DOI 10.1016/j.procs.2010.12.011. **Contributes:** replace equal weights with business weights (score = w_R·R + w_F·F + w_M·M) and extend beyond 3 axes. **Implication:** our equation is essentially an extended-weighted-RFM with **P&L sign** — positive on revenue axes, negative on cost/risk axes; set weights by business reasoning first, tune only lightly vs the public LB. *(Overstated: this entry conflates several sources; use the **idea** of business-reasoned weights, do **not** cite it as one canonical authority in the graded writeup.)*

- **An Exploration of Clustering Algorithms for Customer Segmentation (UK Retail)** — John, Shobayo & Ogunleye (2023) — *Analytics* 2(4):809–823, DOI 10.3390/analytics2040042 (arXiv:2402.04103). **Contributes:** head-to-head on 541,909 records; GMM wins (Silhouette 0.80); standard pipeline = build RFM → log-transform skew → standardize → cluster → profile. **Implication:** prefer **GMM (or rank-transform-then-k-means)** over vanilla k-means on heavy-tailed spend (mind `f7` negatives/refunds); use the high-value segment as an **internal pseudo-ground-truth** to check our score concentrates the same members in its top 20%. *(Scope caution: one dataset's silhouette result — a recipe, not a law.)*

- **Segmenting Bank Customers via RFM Model and Unsupervised ML** — Aliyev, Ahmadov, Gadirli, Mammadova & Alasgarov (2020) — arXiv:2008.08662. **Contributes:** RFM + clustering on real **bank** customer data, profitability/retention framing, k via elbow/silhouette, value-tier profiling. **Implication:** closest-domain precedent; template for cluster profiling — bin members into tiers and show mean spend (`f5`), revolve (`f1`), reward cost (`f4/f21`), risk (`f11`) move **monotonically** across tiers as interpretability evidence.

- **Deep Feature Synthesis** — Kanter & Veeramachaneni (2015) — IEEE DSAA 2015, pp. 1–10, DOI 10.1109/DSAA.2015.7344858. **Contributes:** a small algebra of feature primitives — aggregation (SUM/MEAN/COUNT/STD/MAX) and transform (ratios, normalized differences). **Implication:** build interpretable **ratio/efficiency terms** a raw weighted sum misses: redemption intensity `f21/f4`, category mix `f6–f10 / f5`, benefit-credit burden `(f13+f14+f15+f16)/spend`, engagement `f12/f20`. *(Scope caveat: DFS's relational multi-table synthesis does **not** apply to our single flat table — borrow only the primitive vocabulary.)*

- **Solving the "False Positives" Problem in Fraud Prediction** — Wedge, Kanter, Veeramachaneni, Rubio & Perez (2017) — arXiv:1710.07709 (ECML-PKDD 2017). **Contributes:** automatically-generated **customer-relative aggregate** features (per-customer sums/counts/windowed means, deviations from a member's own baseline) sharply improve card-transaction modeling (demonstrated as a 54% false-positive reduction). **Implication:** favor **within-member normalized** ratios over purely global features where possible. *(Mild caveat: the clean "relative beats global" ablation is weaker than the implication suggests; the demonstrated result is the FP reduction.)*

> **Load-bearing missingness (this theme's key insight):** treat the structured co-missing clusters — `f17/f18` (~60% missing = charge-only members), `f6–f10`, `f4/f21` — as **explicit informative binary indicators / category bins**, not values to impute. The mask itself separates member archetypes. *(The MIA / Random-Indicator references behind this were not in the verified papers array and are not cited individually; the principle is carried by the behavioral-scorecard WOE-on-missing-bins approach in Theme J, which is.)*

### J. Behavioral Scoring & Attrition (deep cost / risk side)

Behavioral scoring scores an **existing** account from its own recent behavior — exactly our setting (23 masked 12-month features, every member already a cardholder). The canon delivers three things our cost/risk side needs: a vocabulary for forward-looking risk/attrition from behavior; the principle that cost terms should be weighted by **profit-at-stake**, not a flat coefficient; and a profit-as-state dynamic that licenses a revenue × risk-discount form.

> **Cross-cutting integrity caveat (from FLAGS):** every cited paper here **fits its model on observed events** (defaults, churn, realized profit/transitions). They supply the **FORM** (hazard, multiplicative discount, per-example cost weighting) — none demonstrate a *label-free* score. Claim structural inspiration, not empirical validation. The feature→hazard mappings below (`f2`→attrition, `f3/f11`→default) are **our domain assumptions**, not paper findings.

**Strongest verified works + contribution + implication:**

- **Credit Scoring and Its Applications (2nd ed.)** — Thomas, Edelman & Crook (2002/2017) — SIAM, DOI 10.1137/1.9781611974560. **Contributes:** defines **behavioral** scoring (vs application scoring) and the additive, binned, WOE log-odds scorecard. **Implication:** frame our deliverable explicitly as a **behavioral profit scorecard** — bin each driver into point contributions whose sum is the score (transparent to auditors), and treat the structured-missing clusters as **their own bins**.

- **Survival Analysis Methods for Personal Loan Data** — Stepanova & Thomas (2002) — *Operations Research* 50(2):277–289, DOI 10.1287/opre.50.2.277.426. **Contributes:** Cox PH h(t|x)=h₀(t)·exp(β'x) on behavioral covariates, plus a **survival-based coarse-classification** binning method; states survival tools "assess aspects of profit as well as default." **Implication:** reuse the FORM — treat `f11`, `f1`, `f3` as a default-hazard linear predictor and use an exp(−hazard)-style factor as a **multiplicative loss-risk discount** on revenue; use survival-based coarse-classification to bin `f11` and the revolve/lend block into risk bands.

- **Customer attrition analysis for financial services using proportional hazard models** — Van den Poel & Lariviere (2004) — *EJOR* 157(1):196–217, DOI 10.1016/S0377-2217(03)00069-9. **Contributes:** PH model of the hazard of a customer **leaving**, driven by interaction frequency, product usage, environmental covariates. **Implication:** build an explicit **attrition discount** — `f2` (cancellation calls, the most direct churn-intent signal), declining engagement (`f12`, `f22/f23`), weak product depth (`f19`, `f20`) raise the hazard; multiply revenue by a retention factor so churn-intent members are discounted out of the top 20% even at high raw spend.

- **A Novel Profit Maximizing Metric for Customer Churn (EMP/EMPC)** — Verbraken, Verbeke & Baesens (2013) — *IEEE TKDE* 25(5):961–973, DOI 10.1109/TKDE.2012.50. **Contributes:** the Expected Maximum Profit measure — integrates per-decision costs/benefits, outputs a score **and an optimal fraction-to-target η\***; shows AUC-optimal models are profit-suboptimal. **Implication:** (1) optimizing **precision@top-20% is a profit-fraction objective** — tune to separate the profitable head, not minimize global rank error; (2) weight cost terms by their **profit consequence**, not raw magnitude. *Caveat (analogy, not theorem):* EMP studies optimal fraction, not precision@k.

- **Example-Dependent Cost-Sensitive Decision Trees** — Bahnsen, Aouada & Ottersten (2015) — *ESWA* 42(19):6609–6619, DOI 10.1016/j.eswa.2015.04.042 (ensemble: arXiv:1505.04637). **Contributes:** a **per-example** cost matrix embedded in tree impurity/pruning, optimizing financial savings. **Implication:** our cost terms must scale with the individual's revenue-at-stake — a cancellation call (`f2`) from a high-spend (`f5`), deep-relationship (`f19/f20`) member is far costlier than from a marginal member → implement as a **revenue × distress-signal interaction**. Validate that the discount predominantly demotes members whose at-risk profit is large. *(Minor: the ESWA paper and the arXiv ensemble are two distinct works; cite separately if used.)*

- **Modelling the profitability of credit cards by Markov decision processes** — So & Thomas (2011) — *EJOR* 212(1):123–130, DOI 10.1016/j.ejor.2011.01.023. **Contributes:** an MDP where states = behavioral-score bands, value = expected discounted profit net of default/attrition, conditioned on current state. **Implication:** the most product-specific (credit-card) justification for our **revenue × risk-discount** structure — "current realized margin × probability of staying in a good behavioral state." *(Caveat: using a dynamic MDP to justify a static one-period discount is a reasonable approximation, not a result the paper proves.)*

---

## 3. Updated design guidance (focused on the new material)

### CLV-canon grounding — how it legitimizes and shapes the equation (and its limits)
- **Adopt the SHAPE, cite the canon.** Berger-Nasr (1998) gives the literal template: per-member `Profit ≈ (revenue terms) − (cost terms)`, then **scaled by a survival/retention factor**. State this is the form Amex graders recognize, with `f11/f3/f2` standing in for (1−retention)/loss probability.
- **Use the Gupta-Lehmann-Stuart persistence multiplier.** Fold a parameter-light `× [r/(1+d−r)]`-style persistence factor onto the annual revenue−cost base, and let the **retention/risk multiplier carry more leverage than marginal spend** (their ~5× retention-vs-margin sensitivity). State it as a **weighting prior**, not a guarantee.
- **Iso-value (Fader-Hardie-Lee 2005) licenses a monotone, many-to-one score** and warns against naive summation — **log/rank-transform** heterogeneous features and allow a **frequency×monetary interaction**.
- **Pareto/NBD + BG/NBD** justify treating sustained activity as forward value and down-weighting latent-inactive members — but **only as legitimacy, not estimators**: we have a single 12-month cross-section, no transaction timestamps, so the stochastic models **cannot be fit**. The frequency-vs-monetary decomposition needs **BG/NBD + Gamma-Gamma**.
- **Rust-Lemon-Zeithaml (2004)** supplies the relationship-equity vocabulary for a positive engagement term (`f13–f16`, `f12`, `f19`) — present as **analogy**, net of its cost.
- **Hard limit:** the canon validates *structure*, never our specific masked-feature→term mapping. Keep that mapping as our own defensible assumption.

### Weighting & normalization — concrete, now-cited options mapped to f1–f23
1. **Sign-orient first (Handbook step):** invert cost/risk indicators (`f2, f3, f4, f11, f13–f16, f21`; handle `f7` refund negatives) so "higher = more profitable" everywhere — a cheap correctness safeguard.
2. **Normalize:** min-max to [0,1] **or rank-transform** each of `f1–f23`. Rank-transform is preferred — it neutralizes the `f11≈0.03` vs `f4≈126K` scale mismatch and the heavy tails.
3. **Weight (objective, label-free):** **CRITIC** as primary (correlation-aware → deflates the collinear `f5–f10` and `f13–f16` clusters), **Shannon-entropy** as a baseline, **equal-weight** as a sanity floor — then **tilt by business P&L sign**.
4. **Aggregate (a business decision):** prefer a **partially-compensatory** aggregator (geometric mean / penalized index) so high spend **cannot** mask high `f11` risk or heavy `f13–f16` cost; benchmark against an arithmetic (fully-compensatory) baseline. Remember weights ≠ importance under non-linear aggregation (Greco 2019).
5. **Alternative engine:** **TOPSIS** — rank by closeness `C_i ∈ [0,1]` to the ideal-profitable profile; plain-language ("% of the way to the ideal member"), scores all 500K, pairs with CRITIC/entropy weights.
6. **Validate with sensitivity (Saisana 2005):** Monte-Carlo over {normalization × weights × aggregation}; report **top-20% membership stability** — our best proxy for generalizing to the hidden 30%.

### Top-k / ranking — what LTR does and does NOT give us
- **Does NOT:** train a ranker. RankNet, ListNet, LambdaMART, LambdaRank all need relevance labels — **inapplicable**. Never claim we "trained a ranker."
- **DOES (evaluation framing):** our metric is **Precision@k at the quintile** — order-insensitive set overlap. **Do not fine-order the top**; the only points come from getting the right ~100,000 members across the **80th-percentile boundary** (LambdaMART's "top matters most" principle).
- **DOES (label-free fusion):** **Reciprocal Rank Fusion** (Cormack 2009) to combine revenue / lend / cost / risk / engagement sub-rankings — scale-free, top-heavy, robust; use as the fusion engine or a benchmark against the weighted sum.
- **DOES (diagnostics):** **SoftRank** perturbation → expected top-20% membership (find borderline members before submitting); **ListNet softmax** → top-k inclusion probabilities (confidence).
- **Framing only, never a guarantee:** "a well-chosen monotone proxy is the principled response to a non-differentiable top-k target" — do not claim a provable bound.

### Segmentation & feature engineering — RFM spine + informative missingness
- **Spine:** an **extended weighted-RFM**, quintile/percentile-rank composite — positive on revenue axes (`f5–f10`, `f1`, `f19`, `f20`), negative on cost/risk axes (`f4/f21`, `f13–f16`, `f3`, `f2`, `f11`).
- **Ratio/efficiency terms (DFS primitives, single-table only):** `f21/f4` (redemption intensity), `f6–f10 / f5` (category mix), `(f13+f14+f15+f16)/spend` (benefit-credit burden), `f12/f20` (engagement).
- **Internal pseudo-ground-truth:** cluster log/rank-transformed features with **GMM** (or rank-then-k-means; bank precedent Aliyev 2020), confirm our score's top 20% concentrates the same high-value members and that tier means move monotonically.
- **Informative missingness (load-bearing):** encode the co-missing clusters as **explicit binary indicators / bins** — `f17/f18` (~60% missing ⇒ charge-only archetype), `f6–f10`, `f4/f21`. The mask separates member archetypes; do **not** impute it away.

### Behavioral / attrition — refining the cost & persistence terms
- **It's behavioral scoring, not application scoring** — frame the deliverable as an additive, binned, interpretable **behavioral profit scorecard** (Thomas-Edelman-Crook).
- **Multiplicative risk-and-retention discount, not a flat dollar subtraction:** a default-hazard linear predictor from `f11/f1/f3` (Stepanova-Thomas) × an attrition-hazard factor from `f2/f12/f22/f23/f19/f20` (Van den Poel-Lariviere), applied as `revenue × survival × retention`.
- **Weight distress by profit-at-stake (example-dependent cost, Bahnsen 2015):** the discount is a **revenue × distress-signal interaction** — penalize a churn signal from a high-value member far more than from a marginal one.
- **Profit-fraction objective (EMP, Verbraken 2013):** tune to **separate the profitable head**, consistent with precision@top-20%.
- **Validation test:** confirm the discount actually **changes WHO lands in the top 20%** and predominantly demotes high-at-risk-profit members. If it only reshuffles the bottom, it isn't earning its place (So-Thomas profit-state framing).

---

## 4. Net-new citations for the graded writeup

- **Berger & Nasr (1998), *J. Interactive Marketing* 12(1):17–30, DOI 10.1002/(SICI)1520-6653...** — the canonical `(revenue − cost) × retention / (1+d)` skeleton; cite as the *form* of our equation.
- **Gupta, Lehmann & Stuart (2004), *JMR* 41(1):7–18, DOI 10.1509/jmkr.41.1.7.25084** — quantitative "retention dominates margin" prior justifying high leverage on the risk/retention multiplier.
- **Fader, Hardie & Lee (2005), *JMR* 42(4):415–430, DOI 10.1509/jmkr.2005.42.4.415** — iso-value: label-free RFM→value, and the warning to log/rank-transform rather than sum raw features.
- **OECD/JRC Handbook on Constructing Composite Indicators (2008), JRC47008, ISBN 978-92-64-04345-9** — the 7-step pipeline as the Framework-sheet skeleton (normalize → weight → aggregate → robustness).
- **Saisana, Saltelli & Tarantola (2005), *JRSS-A* 168(2):307–323, DOI 10.1111/j.1467-985X.2005.00350.x** — Monte-Carlo sensitivity as our no-label validation; report top-20% stability.
- **Cormack, Clarke & Büttcher (2009), SIGIR 2009 pp. 758–759, DOI 10.1145/1571941.1572114** — Reciprocal Rank Fusion: label-free, scale-free fusion of our P&L sub-rankings.

---

## 5. Curated reading list (all included works, by theme)

### F. CLV / Customer-Equity Canon
- **RFM and CLV: Using Iso-Value Curves for Customer Base Analysis** — Fader, Hardie & Lee (2005) — *JMR* 42(4):415–430, DOI 10.1509/jmkr.2005.42.4.415 — *the single best label-free RFM→value citation; licenses a monotone score and warns against naive summation.*
- **Valuing Customers** — Gupta, Lehmann & Stuart (2004) — *JMR* 41(1):7–18, DOI 10.1509/jmkr.41.1.7.25084 — *simplified CLV + sensitivity ranking; weight retention/risk above marginal spend.*
- **Customer Lifetime Value: Marketing Models and Applications** — Berger & Nasr (1998) — *J. Interactive Marketing* 12(1):17–30, DOI 10.1002/(SICI)1520-6653(199824)12:1<17::AID-DIR3>3.0.CO;2-K — *canonical (rev−cost)×retention/(1+d) template.*
- **Counting Your Customers: Who Are They and What Will They Do Next?** — Schmittlein, Morrison & Colombo (1987) — *Management Science* 33(1):1–24, DOI 10.1287/mnsc.33.1.1 — *Pareto/NBD; legitimacy for activity-as-value and latent-dropout down-weighting.*
- **"Counting Your Customers" the Easy Way (BG/NBD)** — Fader, Hardie & Lee (2005) — *Marketing Science* 24(2):275–284, DOI 10.1287/mksc.1040.0098 — *tractable frequency process; split how-often from how-much (decomposition needs +Gamma-Gamma).*
- **Return on Marketing: Using Customer Equity to Focus Marketing Strategy** — Rust, Lemon & Zeithaml (2004) — *J. Marketing* 68(1):109–127, DOI 10.1509/jmkg.68.1.109.24030 — *customer equity = Σ CLV; relationship-equity vocabulary for the engagement term.*

### G. Learning to Rank & Top-k Metric Optimization
- **Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods** — Cormack, Clarke & Büttcher (2009) — SIGIR 2009 pp. 758–759, DOI 10.1145/1571941.1572114 — *label-free, scale-free, top-heavy fusion — our core fusion mechanism.*
- **SoftRank: Optimising Non-Smooth Rank Metrics** — Taylor, Guiver, Robertson & Minka (2008) — WSDM 2008 pp. 77–86, DOI 10.1145/1341531.1341544 — *Gaussian-smoothed scores → expected top-20% membership; the right stability test.*
- **From RankNet to LambdaRank to LambdaMART: An Overview** — Burges (2010) — MSR-TR-2010-82 — *"errors near the top matter most" → calibrate around the 80th-percentile cutoff.*
- **Learning to Rank using Gradient Descent (RankNet)** — Burges et al. (2005) — ICML 2005 pp. 89–96, DOI 10.1145/1102351.1102363 — *legitimizes monotone scoring + sorted ranking; needs labels as a trainer (inapplicable).*
- **Learning to Rank: From Pairwise to Listwise (ListNet)** — Cao, Qin, Liu, Tsai & Li (2007) — ICML 2007 pp. 129–136, DOI 10.1145/1273496.1273513 — *softmax-over-scores → top-k inclusion probabilities for confidence diagnostics.*

### H. Composite Indicators & MCDA
- **Handbook on Constructing Composite Indicators: Methodology and User Guide** — Nardo, Saisana, Saltelli, Tarantola, Hoffmann & Giovannini (2008) — OECD/JRC, JRC47008, ISBN 978-92-64-04345-9 — *the 7-step pipeline; the Framework-sheet skeleton.*
- **On the Methodological Framework of Composite Indices** — Greco, Ishizaka, Tasiou & Torrisi (2019) — *Social Indicators Research* 141(1):61–94, DOI 10.1007/s11205-017-1832-9 — *weighting/aggregation/robustness survey; objective weights + partial compensation.*
- **Determining objective weights: the CRITIC method** — Diakoulaki, Mavrotas & Papayannakis (1995) — *Computers & OR* 22(7):763–770, DOI 10.1016/0305-0548(94)00059-H — *correlation-aware weighting; deflates the collinear spend cluster.*
- **Constructing composite indicators with Shannon entropy** — R. Karagiannis & G. Karagiannis (2020) — *Socio-Economic Planning Sciences* 70:100701, DOI 10.1016/j.seps.2019.03.007 — *label-free entropy weighting; default objective baseline.*
- **Multiple Attribute Decision Making: Methods and Applications (TOPSIS)** — Hwang & Yoon (1981) — Springer LNEMS Vol. 186, DOI 10.1007/978-3-642-48318-9 — *rank by closeness to the ideal-profitable profile; interpretable C∈[0,1].*
- **Uncertainty and sensitivity analysis ... for composite indicators** — Saisana, Saltelli & Tarantola (2005) — *JRSS-A* 168(2):307–323, DOI 10.1111/j.1467-985X.2005.00350.x — *Monte-Carlo robustness = our no-label validation.*

### I. Segmentation & Financial Feature Engineering
- **Strategic Database Marketing (RFM 5×5×5)** — Hughes (1994) — McGraw-Hill, ISBN 0071456805 — *origin of the quintile RFM model.*
- **Optimal Selection for Direct Mail (first peer-reviewed RFM)** — Bult & Wansbeek (1995) — *Marketing Science* 14(4):378–394, DOI 10.1287/mksc.14.4.378 — *formal RFM/top-quintile basis; auto-normalizing rank composite.*
- **RFM and CLV: Iso-Value Curves** — Fader, Hardie & Lee (2005) — *JMR* 42(4):415–430, DOI 10.1509/jmkr.2005.42.4.415 — *(cross-listed F)* RFM aggregates ≈ sufficient statistics; defends a closed-form score over a model.
- **Weighted/extended-RFM (WRFM/eRFM)** — *Procedia CS* 3 (2011), DOI 10.1016/j.procs.2010.12.011 — *business-reasoned weights + extra axes; use the **idea**, not as one canonical authority (conflated entry).*
- **An Exploration of Clustering Algorithms for Customer Segmentation (UK Retail)** — John, Shobayo & Ogunleye (2023) — *Analytics* 2(4):809–823, DOI 10.3390/analytics2040042 (arXiv:2402.04103) — *GMM > k-means on skewed spend; pseudo-ground-truth recipe.*
- **Segmenting Bank Customers via RFM Model and Unsupervised ML** — Aliyev et al. (2020) — arXiv:2008.08662 — *closest-domain (bank) RFM+clustering precedent; value-tier profiling.*
- **Deep Feature Synthesis** — Kanter & Veeramachaneni (2015) — IEEE DSAA 2015 pp. 1–10, DOI 10.1109/DSAA.2015.7344858 — *ratio/aggregation primitive vocabulary (single-table use only).*
- **Solving the "False Positives" Problem in Fraud Prediction** — Wedge et al. (2017) — arXiv:1710.07709 (ECML-PKDD 2017) — *customer-relative aggregate features in the card domain.*

### J. Behavioral Scoring & Attrition
- **Credit Scoring and Its Applications (2nd ed.)** — Thomas, Edelman & Crook (2002/2017) — SIAM, DOI 10.1137/1.9781611974560 — *defines behavioral scoring + the additive binned scorecard form.*
- **Survival Analysis Methods for Personal Loan Data** — Stepanova & Thomas (2002) — *Operations Research* 50(2):277–289, DOI 10.1287/opre.50.2.277.426 — *Cox PH discount + survival-based coarse-classification binning.*
- **Customer attrition analysis for financial services using proportional hazard models** — Van den Poel & Lariviere (2004) — *EJOR* 157(1):196–217, DOI 10.1016/S0377-2217(03)00069-9 — *attrition-hazard form for the retention discount.*
- **A Novel Profit Maximizing Metric for Customer Churn (EMP/EMPC)** — Verbraken, Verbeke & Baesens (2013) — *IEEE TKDE* 25(5):961–973, DOI 10.1109/TKDE.2012.50 — *profit-fraction objective; cost-benefit weighting.*
- **Example-Dependent Cost-Sensitive Decision Trees** — Bahnsen, Aouada & Ottersten (2015) — *ESWA* 42(19):6609–6619, DOI 10.1016/j.eswa.2015.04.042 (ensemble arXiv:1505.04637) — *per-example costs → revenue × distress interaction.*
- **Modelling the profitability of credit cards by Markov decision processes** — So & Thomas (2011) — *EJOR* 212(1):123–130, DOI 10.1016/j.ejor.2011.01.023 — *credit-card profit-MDP; licenses revenue × risk-discount.*

---

## 6. Honest gaps remaining

- **Excluded as unverifiable this round** (canonical and high-confidence, but not independently confirmed — do **not** cite as verified in the graded writeup): **Liu (2009)** LTR survey (FnT IR 3(3):225–331); **Wang et al. (2018)** LambdaLoss (CIKM, DOI 10.1145/3269206.3271784); the **Precision@k** textbook definition.
- **Two real CLV models not in the verified papers array** → cite only after separate verification: **Pfeifer & Carraway (2000)** Markov-chain recency-state CLV (*J. Interactive Marketing* 14(2):43–55) and **Venkatesan & Kumar (2004)** CLV-based customer selection. Both fit our single-cross-section framing well; verify before use.
- **Dropped for author mis-attribution:** "Unsupervised Submodular Rank Aggregation on Score-based Permutations" (arXiv:1707.01166) — the scout's "Jin, Cevher" is wrong (actual: Qi, Liu, Tejedor, Kamijo). The RRF citation (Cormack 2009) already covers label-free fusion; only re-introduce the submodular paper if the corrected attribution is independently checked.
- **No verified Mazziotta-Pareto (MPI/AMPI) primary source** — if a non-compensatory penalized aggregator is cited specifically, add and verify Mazziotta & Pareto rather than leaning on the Handbook/Greco.
- **Conflated/loose attributions to handle carefully:** the **WRFM/eRFM** entry bundles several sources — use the *idea*, not one authority; the **BG/NBD** frequency/monetary decomposition must be credited to **BG/NBD + Gamma-Gamma**; the **Bahnsen ESWA paper vs its arXiv ensemble** are two distinct works.
- **Still uncited / out of reach:** dedicated **informative-missingness / MNAR primary sources** (Twala MIA; Random-Indicator imputation) were referenced in the segmentation theme but were **not** in any verified papers array — the principle currently rides on Theme J's scorecard WOE-binning; a primary MIA citation remains to be obtained (likely Semantic Scholar / paywalled). Several OR/marketing sources here are **paywalled** (INFORMS, Elsevier, Springer, Wiley) — only abstracts/DOIs are confirmed, not full-text re-derivation of every quoted formula (entropy `E_j`, CRITIC `w_j`, TOPSIS `C_i` are standard textbook forms — re-derive when implementing).
- **The deepest unsettled point (unchanged by this round):** none of these works validate that **our masked-feature→P&L-term mapping is correct** (e.g., that `f11` is a clean retention proxy, or `f13–f16` usage = relationship equity). The canon legitimizes the **structure**; the mapping stays our own defensible assumption, validated only by **top-20% stability under sensitivity analysis**, never by a ground-truth label.


---
---

<!-- ROUND-3 ADDENDUM appended 2026-06-27 from workflow w5q2bjobv (9 agents). Spot-checked: arXiv 1303.3257 (Parisi SML) & 1605.07723 (Ratner/Snorkel) confirmed via get_paper. Round-3 verdict: diminishing returns reached -> move to implementation. Journal DOIs not independently re-fetched; flagged soft numerals listed in §6. -->

# Round-3 Addendum #2 — Amex Premier Profitability Literature Review

*Themes K–N: resolving flagged primaries, premium/charge-card economics & share-of-wallet, rewards-liability/benefit cost, and validating label-free scores. Inclusion rule: only works verified `supported` (or `overstated`, flagged inline) are cited; `unverifiable` items are dropped from the citation list but, for Theme K, each previously-flagged work's resolution is stated explicitly.*

---

## 1. What round 3 adds

- **Six of seven previously-flagged primaries are now confirmed with DOIs/venues**; the seventh (Random Indicator MNAR imputation) is real as a *method* but its "credit-scoring" framing stays unverifiable, so it is dropped from our citations.
- **A primary, peer-reviewed defense of "missingness-as-signal":** MIA (Twala–Jones–Hand 2008) justifies encoding our structured missing flags (charge-only `f17`/`f18`, co-missing `f6`–`f10`, `f4`/`f21`) as their own signed terms rather than filling with 0.
- **A citable non-compensatory aggregator (AMPI, Mazziotta–Pareto 2018):** arithmetic mean of goalpost-normalized drivers *minus* a CV-based imbalance penalty — a defensible alternative to plain weighted sum that down-ranks lopsided members (huge spend but extreme risk) and a clean scheme for mixing scales (`f11`≈0.03 with `f4`≈126K).
- **Premium/charge-card "business physics":** profit on this product is interchange-on-spend-dominated, rewards + lifestyle credits consume 60%+ of premium-card revenue, and the transactor/revolver split governs where margin sits — so raw `f5` is the *wrong* top-20% sort key and reward/credit cost must be *netted*, not ignored.
- **A label-free share-of-wallet template (Glady–Croux 2009):** size-of-wallet and share-of-wallet are recoverable from *internal transaction counts alone* — academic cover for a "wallet-capture" term built from `f5`–`f10` plus breadth signals `f19`/`f20` *without inventing a fake label*.
- **Sharper cost-side machinery for rewards:** `f4` (balance) is a *contingent* liability = Points × Redemption-Rate × Cost-per-Point; `f21` (redeemed) is the near-certain realized cost; a ~17–18% breakage benchmark gives a defensible 80–90% redemption-discount band; `f13`–`f16` are utilization-driven costs (unused credits are breakage in the issuer's favor).
- **A four-family label-free validation protocol** for the most-graded part of the problem: spectral agreement-across-constructions (Parisi–Nadler), composite-indicator robustness/Sobol (OECD/Saisana), bootstrap rank-stability (challengeR), and weak-supervision proxy labels + Lorenz/Gini concentration as sanity checks.
- **Net new, on-theme, confirmed primaries:** MIA, AMPI, Pfeifer–Carraway (Markov migration as framing), Du–Kamakura–Mela, Glady–Croux, Jang–Prasad–Ratchford, So–Thomas–Seow–Mues, the Fed FEDS Note + Report to Congress, the CAS rewards-actuarial paper, Chun–Iancu–Trichakis, CFPB rewards spotlight, IATA IFRS-15 guidance, and the full label-free validation set (Parisi, Jaffe, Saisana, OECD, challengeR, Ratner/Snorkel, Goix).

---

## 2. Per-theme findings (K–N)

### K. Resolving flagged / unverified primaries (confirm-or-drop)

Verification pass on seven flagged primaries. **Six confirmed, one stays partly-unverifiable.** Three of the confirmed works are real but **overlap rounds 1–2** and must NOT be re-counted as new contributions (CLV canon and Learning-to-Rank). The genuinely new, on-theme primaries are MIA, AMPI, and Pfeifer–Carraway.

- **Modeling Customer Relationships as Markov Chains** — Pfeifer & Carraway (2000), *Journal of Interactive Marketing* 14(2):43–55, DOI 10.1002/(SICI)1520-6653(200021)14:2<43::AID-DIR4>3.0.CO;2-H. **Resolution: now confirmed with DOI/venue** (Wiley, ScienceDirect, ProQuest).
  - *Contributes:* customer value as a Markov chain — discrete states, a one-step transition matrix, a per-state cash-flow vector, closed-form discounted lifetime value; argued as more flexible than retention-rate (geometric) CLV.
  - *Implication:* not trainable for us (no label, single 12-month snapshot), but a reusable **framing**: treat behavioral archetypes (charge-only `f17`/`f18`-missing vs revolver vs heavy-redeemer `f4`/`f21`) as "states" with a defensible revenue-minus-cost value-per-state — more interpretable for the graded writeup than a flat weighted sum. Include only as the specific Markov-migration variant, not generic CLV.

- **Good Methods for Coping with Missing Data in Decision Trees (MIA)** — Twala, Jones & Hand (2008), *Pattern Recognition Letters* 29(7):950–956, DOI 10.1016/j.patrec.2008.01.010. **Resolution: now confirmed with DOI/venue** (ScienceDirect, Scholar, scispace, ResearchGate). *Single most actionable verified work.*
  - *Contributes:* "Missingness Incorporated in Attributes" — instead of imputing, send missing values deliberately left/right and let missingness itself be a candidate split; generalizes the missing-indicator idea to continuous and MNAR data; empirically competitive with EM multiple imputation but simpler.
  - *Implication:* primary justification for our missingness-as-signal stance. Our clusters are structural (`f17`/`f18` ~60% missing = charge-only; `f6`–`f10` co-miss; `f4`/`f21` co-miss). The principled move is **not fill-with-0** but to encode the missing flag as its own signed term in the score (e.g. an explicit "charge-only" indicator with its own weight). Strong citation for the writeup's missing-value section; defends directly against the fill-with-0 pitfall CLAUDE.md warns about.

- **Measuring Well-Being Over Time: The Adjusted Mazziotta–Pareto Index (AMPI)** — Mazziotta & Pareto (2018), *Social Indicators Research* 136(3):967–976, DOI 10.1007/s11205-017-1577-5. **Resolution: now confirmed with DOI/venue** (SpringerLink, IDEAS/RePEc; CRAN `Compind::ci_ampi` implements it).
  - *Contributes:* non-compensatory aggregation — goalpost min-max rescaling, arithmetic mean, then *subtract* a CV-based penalty so an imbalanced indicator profile cannot fully compensate. Used by Italian ISTAT for equitable well-being.
  - *Implication:* a citable alternative to plain weighted sum for combining heterogeneous drivers (spend `f5`–`f10`, revolve `f1`, lend `f17`/`f18`, reward-cost `f4`/`f21`, benefit-credit `f13`–`f16`, risk `f11`/`f3`). A truly profitable Premier member is plausibly *balanced* (high spend AND low risk AND moderate reward cost). An AMPI-style imbalance penalty on the top quintile could improve Top-20% precision by down-ranking lopsided members; goalpost normalization is a clean scheme to mix `f11`≈0.03 with `f4`≈126K. **Worth an A/B experiment vs the weighted-sum baseline.** *Flag:* verify the `[70,130]` goalpost range against the Springer PDF before quoting it verbatim — the standard MPI/AMPI rescaling and CRAN confirm goalpost min-max, so it is almost certainly correct, but it was not independently re-echoed this pass.

- **Random Indicator (RI) Imputation for MNAR data** — Jolani & van Buuren, arXiv:2404.14534 (2024). **Resolution: method confirmed to EXIST (arXiv abstract matches exactly: observed part ~normal, missingness logistic, iterative draws of imputations + a pseudo response indicator, MNAR adjustment estimated from data); its stated "credit-scoring" application STAYS UNVERIFIABLE** (only a generic real dataset in the abstract; no source ties RI to credit scoring). **Decision: DROP from citations.** Prefer the simpler MIA flag-encoding; mention RI only if a reviewer challenges why we did not run an MNAR imputation we cannot validate without a label.

**Overlap — confirmed real but do NOT count as new (covered in rounds 1–2):**
- **Learning to Rank for Information Retrieval (survey)** — Liu (2009), *Foundations and Trends in IR* 3(3):225–331, DOI 10.1561/1500000016. Confirmed real; foundational survey for the already-covered LTR theme. Keep only as a vocabulary anchor; we have no relevance labels to train a ranker.
- **The LambdaLoss Framework for Ranking Metric Optimization** — Wang, Li, Golbandi, Bendersky & Najork (2018), CIKM '18, pp. 1313–1322, DOI 10.1145/3269206.3271784. Confirmed real; inside already-covered LambdaMART/LTR. **Keep the insight, not the algorithm:** our metric (Top-20% overlap = precision@top-quintile) is exactly the discontinuous top-k metric LambdaLoss surrogate-optimizes, which validates concentrating calibration effort *at the 80th-percentile boundary* rather than on global rank fidelity.
- *(Venkatesan–Kumar 2004 is also confirmed-real-but-overlapping CLV canon; not re-fetched this round, accept conservative overlap framing; confirm venue/DOI before citing directly.)*

### L. Premium / charge-card economics & share-of-wallet

Supplies the Amex-specific business physics our score must encode, and a label-free way to read relationship breadth.

- **Size and Share of Customer Wallet** — Du, Kamakura & Mela (2007), *Journal of Marketing* 71(2):94–113, DOI 10.1509/jmkg.71.2.94.
  - *Contributes:* formalizes size-of-wallet (total category spend across all providers) vs share-of-wallet (focal firm's fraction); empirically finds focal-firm spend correlates *weakly* with competitor spend, and a small fraction of customers hold most external wallet.
  - *Implication:* the most profitable Premier members are not just high absolute spenders but those whose spend reflects a *large captured share of a large wallet*. Treat `f5`/`f6`–`f10` as size-of-wallet proxies and `f19`/`f20` as share-of-wallet/breadth proxies. The weak-correlation finding is a direct caution: **do NOT assume high `f5` = dominant captured share.**

- **Predicting Customer Wallet Without Survey Data** — Glady & Croux (2009), *Journal of Service Research* 11(3):219–231, DOI 10.1177/1094670508328983 (working paper PDF at KU Leuven). *Strongest match to the no-label constraint.*
  - *Contributes:* a **label-free** share-of-wallet method — model unobserved total transactions (latent size-of-wallet) from customer characteristics, treat observed focal transactions as Binomial draws whose success probability *is* the share-of-wallet; estimates both from internal data only.
  - *Implication:* academic cover to build an interpretable "wallet-capture" term where observed Amex spend (`f5`–`f10`) is the captured count and breadth/engagement signals (`f19`/`f20`, low cancellation `f2`, high logins `f12`) scale an implied latent total — *without inventing a fake profitability label*. **Flag:** we adopt this as analogy/inspiration, not a literal reimplementation of the binomial estimator (we lack the competitor-transaction structure their model assumes); say so in the writeup.

- **Consumer Spending Patterns across Firms and Categories** — Jang, Prasad & Ratchford (2016), *International Journal of Research in Marketing* 33(1):123–139, DOI 10.1016/j.ijresmar.2015.06.005.
  - *Contributes:* extends SOW estimation across multiple categories and firms; yields category-level size/share of wallet and links to untapped potential and loyalty.
  - *Implication:* our spend is already disaggregated (`f6`–`f10`, with refunds negative in `f7`). Justifies a **category-breadth / spend-diversity term**: a member concentrating many categories on the Premier card signals higher captured wallet and stickiness than one with the same `f5` in a single category. Reinforces netting `f7` refunds out of genuine volume. (We borrow the per-category-breadth justification only — not the heavy econometric machinery.)

- **Using a transactor/revolver scorecard to make credit and pricing decisions** — So, Thomas, Seow & Mues (2014), *Decision Support Systems* 59:143–151, DOI 10.1016/j.dss.2013.11.002.
  - *Contributes:* a transactor/revolver classification scorecard + a Good/Bad scorecard over revolvers, with a segment-specific profit model — transactors earn the issuer merchant-service-charge (interchange) only; revolvers earn interest but carry higher default risk; respecting the split beats one linear weight.
  - *Implication:* maps directly onto our feature split and argues for a **piecewise/segment-aware profit term**, not a single linear revolve coefficient. Charge-only/transactor members (low/absent `f1`, missing `f17`/`f18`) earn interchange-on-spend, so their score should weight net spend and reward-cost efficiency; revolver/lender members (present `f1`/`f17`/`f18`) add an interest-revenue term discounted by risk (`f11`, `f3`). **Flag:** distinct from the rounds-1–2 So–Thomas behavioral-scoring work (different co-authors Seow+Mues, different year, explicit profit-by-segment) — additive, do not double-count.

- **Credit Card Profitability (FEDS Note)** — Adams, Bord & Katcher (2022), Federal Reserve Board, FEDS Notes, Sep 9 2022, DOI 10.17016/2380-7172.3100 (URL: federalreserve.gov/econres/notes/feds-notes/credit-card-profitability-20220909.html).
  - *Contributes:* FR Y-14M analysis — transactors spend the MOST per month (~$825 vs $640 light, $200 heavy revolvers) and drive ~40% of purchase volume, yet revolvers capture the majority of profitability via interest income.
  - *Implication:* empirically anchors weights: the highest spenders are NOT the most profitable on a standard interest-driven card, so a naive "rank by `f5`" misorders the top quintile. **Flag (attribution):** this is a *revolving-credit* portfolio source; the "spend-centric, weaker lending engine" framing for the Premier *charge* card is our product-physics inference — attribute it to charge-card logic, not to the Fed. Net effect: keep a strong, well-justified spend term but pair it with a revolve/lend term (`f1`/`f17`/`f18`) and a risk discount, and net reward cost.

- **Report to the Congress on the Profitability of Credit Card Operations of Depository Institutions** — Federal Reserve Board (annual; mandated by Sec. 8, Fair Credit and Charge Card Disclosure Act of 1988). URL: federalreserve.gov/publications/credit-card-profitability.htm.
  - *Contributes:* long-running portfolio-level ROA and revenue/expense benchmarks for card-specialist institutions (~3.4–4.0% ROA for large card banks vs ~1.3–1.5% all banks).
  - *Implication:* a citable **calibration/credibility anchor** to sanity-check that our revenue-minus-cost framework yields business-plausible relative margins. It is portfolio-aggregate, so it informs sign/scale of cost terms, not individual ranking.

- **The Illusion of Premium Card Profitability** — Flagship Advisory Partners (consultancy insight, ~2024). URL: insights.flagshipadvisorypartners.com/the-illusion-of-premium-card-profitability.
  - *Contributes:* premium-card P&L decomposition — points + lifestyle credits consume 60%+ of revenue, collapsing net income to under ~$200/account.
  - *Implication:* justifies netting reward cost (`f4`/`f21`) and benefit credits (`f13`–`f16`) against spend revenue — a thin-margin transactor with rich rewards can rank below a lower-spender. **Flag:** practitioner, not peer-reviewed; cite as an industry *illustration* of premium-card economics, not as primary empirical evidence.

### M. Rewards liability, breakage & benefit-cost modeling

Sharpens the COST side: `f4` (balance), `f21` (redeemed), and benefit credits `f13`–`f16`. Core insight: an outstanding rewards balance is a *contingent* liability, not a realized cost.

- **Loyalty Rewards and Gift Card Programs: Basic Actuarial Estimation Techniques** — Gault, Llaguno & Menard (2012), Casualty Actuarial Society E-Forum, Summer 2012 (PDF on casact.org). *The single most defensible structural claim in the theme.*
  - *Contributes:* the master identity **Cost = Points × Redemption-Rate × Cost-per-Point**, with breakage = 1 − redemption rate; estimation via point-redemption triangles by issuance period (chain-ladder); distinguishes accrued-cost vs deferred-revenue valuation.
  - *Implication:* `f4` is a contingent liability — its cost term should be `f4 × (expected redemption probability) × (per-point cost)`, while `f21` (already redeemed) carries weight ≈1. With no per-member redemption triangle, use **`f21/f4` (or `f21/(f4+f21)`) as a member-level redemption-propensity proxy**: high ratio = points convert to cost; low ratio = likely breakage and cheaper than face value. *(The proxy is our extrapolation, defensibly grounded but not literally in the paper.)*

- **Loyalty Program Liabilities and Point Values** — Chun, Iancu & Trichakis (2020), *Manufacturing & Service Operations Management* 22(2):223–259, DOI 10.1287/msom.2018.0748. **OVERSTATED-numeral flag inline.**
  - *Contributes:* DP model of points under IFRS-15 deferred-revenue accounting; optimal point value tracks "profit potential = realized cash flows + outstanding deferred revenue," so liability cost ties to the member's own revenue stream, not a flat per-point charge.
  - *Implication:* make the `f4` cost term **revenue-contingent** — a high balance held by a high-spend member (`f5`–`f10`) is "covered" by profit potential and is less of a net drag than the same balance on a low-spend member. Express reward cost as a fraction of accrued spend / scale the `f4` penalty down where revenue features are high. **OVERSTATED:** the specific "Delta LP liability jumped from $412M to $2.4B on switching to IFRS-15" figure is unverified (conflicts with Delta's ~$8.8B 2024 deferred LP balance) — drop or re-source it; the structural point (deferred-revenue ≫ incremental-cost method) is valid.

- **Credit Card Rewards (Issue Spotlight)** — U.S. CFPB, May 2024 (files.consumerfinance.gov; + Circular 2024-07).
  - *Contributes:* regulator-grade evidence on breakage mechanics — devaluation, revocation/forfeiture on closure, redemption friction; consumers lose "hundreds of millions of dollars" of earned rewards annually.
  - *Implication:* supports a redemption-discount well *below* 100% on `f4`, and pairing high `f2` (cancellation/attrition calls) with high `f4` (attriting members often forfeit balances) to lower expected cost further. **Flag:** qualitative complaint analysis — it supports "discount below 100%" *directionally* but does NOT itself supply a breakage % (the 17–18% number comes from IATA/airline sources; do not attribute it to CFPB).

- **Learning Fair and Effective Points-Based Rewards Programs** — Hssaine, Hu & Pike-Burke (2025), arXiv:2506.03911.
  - *Contributes:* theoretical model where customers accumulate toward a redemption threshold; quantifies cost of a single threshold (≤ factor 1+ln2 vs personalized) and gives low-regret threshold-learning algorithms.
  - *Implication:* redemption is **threshold-driven** — small balances may never clear a practical threshold (near-zero expected cost); large balances near a redemption point approach full cost. Supports a **concave/threshold transform on `f4`** rather than a linear one. (Structural, not a calibrated number.)

- **Modeling User Redemption Behavior in Complex Incentive Digital Environment** — Matsui, Teramoto, Motohashi & Tsurumi (2025), arXiv:2509.14508.
  - *Contributes:* empirical large-scale finance-app study — point usage correlates with demographics/shopping style; redemption propensity is predictable from behavioral signals.
  - *Implication:* modulate the expected-cost weight on `f4` per member using engagement features already in the data — `f12` (logins), `f22`/`f23` (email), and the `f21/f4` ratio. Engaged members → more likely to redeem (full cost); disengaged accumulators → more likely to break (discounted cost). *(Mapping to our features is our inference, justified by the paper, not stated by it.)*

- **IATA Industry Accounting Working Group Guidance: IFRS 15** — IATA IAWG (2018), iata.org (corroborated by AA/Delta/United 2024 10-K loyalty disclosures). **OVERSTATED-numeral flag inline.**
  - *Contributes:* points as a separate performance obligation, deferred as a liability, released to revenue on redemption OR expiry (breakage); incremental-cost formula = marginal fulfilment cost × outstanding points × (1 − breakage); **real breakage benchmark ~17–18%** for two US airlines.
  - *Implication:* gives the concrete breakage anchor for the `f4` discount and the formula structure to mirror for `f4` and for benefit credits `f13`–`f16`. For `f13`–`f16` (lounge/airline/cab/entertainment), cost is **utilization-driven** — observed magnitude already reflects usage, so enter them on the cost side scaled by utilization (an issued-but-unused credit is breakage in the issuer's favor; low utilization is a margin tailwind). **OVERSTATED:** the specific per-airline 2024 liability dollars (AA $10.1B, Delta $8.7B, United $7.9B) drift from actual 10-Ks (AA ~$9.6B, Delta ~$8.8B deferred, United ~$7.1B deferred) — the headline **17–18% breakage IS confirmed**; cite the per-airline dollars loosely or correct them.

- **The Redemption Behavior of Loyalty Points and Customer Lifetime Value** — *Journal of the Korean Operations Research and Management Science Society* (2014), KoreaScience JAKO201430756851448.
  - *Contributes:* RFM computed specifically on a customer's *redemption* behavior improves prediction of future purchases.
  - *Implication:* supports using redemption-recency/frequency proxies (`f21/f4` plus engagement `f12`, `f22`/`f23`) as a per-member redemption-propensity signal feeding the `f4` discount.

### N. Validating label-free / unsupervised scores

The most-graded part of the problem: proving a constructed score is "good" with no label. Four families give a defensible protocol.

- **Ranking and combining multiple predictors without labeled data (Spectral Meta-Learner)** — Parisi, Strino, Nadler & Kluger (2014), *PNAS* 111(4):1253–1258, DOI 10.1073/pnas.1219097111 (arXiv:1303.3257). *Closest primary result to our exact setting.*
  - *Contributes:* given only the predictions of several conditionally-independent scorers over unlabeled data, the off-diagonal of their prediction-covariance matrix is rank-one and its **leading eigenvector ranks the predictors by accuracy**; yields a meta-scorer beating majority vote — no labels.
  - *Implication:* build 3–5 deliberately semi-independent profitability scorers (spend/interchange, revolve+lend interest, risk-discount, benefit-cost) over `f1`–`f23`, compute their agreement-covariance, take the leading eigenvector to **rank which sub-score most likely tracks Amex's hidden truth** and weight the blend. **Load-bearing caveat:** our scorers share features, so conditional independence is only approximate — report the spectral ranking as *corroborating evidence among scorers*, not proof of which matches the hidden truth.

- **Estimating the Accuracies of Multiple Classifiers Without Labeled Data** — Jaffe, Nadler & Kluger (2015), AISTATS, PMLR v38:407–415 (arXiv:1407.7644).
  - *Contributes:* consistent, efficient spectral algorithms estimating each predictor's accuracy and class balance from unlabeled data, with error bounds.
  - *Implication:* a defensible, data-grounded (not purely judgmental) estimate of how reliable each sub-score is, feeding our convergent-validity argument. Same shared-feature independence caveat applies — triangulating signal, not a point estimate.

- **Uncertainty and Sensitivity Analysis Techniques as Tools for the Quality Assessment of Composite Indicators** — Saisana, Saltelli & Tarantola (2005), *JRSS Series A* 168(2):307–323, DOI 10.1111/j.1467-985X.2005.00350.x. *Highest-value, lowest-risk citation for the graded interpretability section.*
  - *Contributes:* the canonical way to validate a composite index with no outcome label — Monte-Carlo over modeling choices (normalization, weights, aggregation, imputation) + variance-based Sobol sensitivity, reporting rank confidence intervals.
  - *Implication:* our score IS a composite indicator with no label. Randomize normalization (z vs rank vs robust-scale), weight vector, and missing-value rule across thousands of runs; report the fraction of members whose Top-20% membership is stable and a Sobol attribution of which choices move the ranking most — turning "we picked these weights" into a quantified robustness claim.

- **Handbook on Constructing Composite Indicators: Methodology and User Guide (OECD/JRC)** — Nardo, Saisana, Saltelli, Tarantola, Hoffmann & Giovannini (2008), OECD, ISBN 978-92-64-04345-9.
  - *Contributes:* the 7-step standard — theoretical framework → select variables → impute missing → multivariate analysis → normalize → weight & aggregate → present/robustness — plus convergent-validity checks.
  - *Implication:* the methodological backbone and vocabulary for the entire Framework writeup. Map our pipeline onto its steps and cite it — directly earns interpretability/integrity credit and pre-empts gaming concerns from auditors.

- **Methods and open-source toolkit for analysing and visualizing challenge results (challengeR)** — Wiesenfarth, Reinke, Landman, Maier-Hein et al. (2021), *Scientific Reports* 11:2369, DOI 10.1038/s41598-021-82017-6 (arXiv:1910.05121). Companion: **"Why rankings of biomedical image analysis competitions should be interpreted with care"** — Maier-Hein et al. (2018), *Nature Communications* 9:5217, DOI 10.1038/s41467-018-07619-7.
  - *Contributes:* a bootstrap rank-stability protocol — resample test cases b≈1000 times, recompute the ranking each time, report bootstrap rank distribution, Kendall-τ vs the point ranking, and rank confidence intervals.
  - *Implication:* directly operationalizes our Top-20%-overlap metric internally with no label — resample the 500K with replacement, recompute the Top-20% set each time, and report each member's bootstrap retention frequency + Kendall-τ. **Our best internal proxy for "will the public-70% Top-20% hold on the hidden 30%?"** and a guard on the 10-submission budget. **Flag:** the bootstrap resamples *test cases* in the paper; resampling the 500K members is our valid adaptation — describe it as such (and use the precise companion title above, "image analysis competitions").

- **Data Programming: Creating Large Training Sets, Quickly** — Ratner, De Sa, Wu, Selsam & Ré (2016), NeurIPS 29, pp. 3567–3575 (arXiv:1605.07723). *(Snorkel.)*
  - *Contributes:* weak supervision — noisy labeling functions denoised by a generative model that infers each LF's accuracy/dependency from agreements alone, emitting probabilistic labels with consistency guarantees.
  - *Implication:* manufacture a *soft proxy* "high-profit" label from business rules as LFs (e.g. "high spend `f5` AND low risk `f11` → profitable"; "heavy revolve `f1`+`f17`/`f18` with low collection-calls `f3` → profitable"; "high benefit-credit use `f13`–`f16` with low spend → unprofitable"), fit a label model, and use the proxy **ONLY to sanity-check / convergent-validate** the equation's Top-20% — *never as a training target.* **Flag:** LF conditional-independence is violated (rules share features) — a triangulating signal, not a point estimate.

- **How to Evaluate the Quality of Unsupervised Anomaly Detection Algorithms? (Mass-Volume & Excess-Mass curves)** — Goix (2016), ICML Anomaly Detection workshop, arXiv:1607.01152.
  - *Contributes:* two label-free criteria (Excess-Mass, Mass-Volume) that discriminate between scoring functions almost as well as ROC/PR using only unlabeled data.
  - *Implication:* a label-free **tie-breaker** between two candidate frameworks — does framework A carve out a tighter, more separated "profitable minority" than B? A Lorenz/Gini concentration check is the simpler in-house analogue. **Flag:** the Lorenz/Gini simplification is *our* device "in the spirit of" Goix — do NOT attribute a Gini/CAP check to Goix, which proposes EM/MV specifically.

- *(VB-Score, arXiv:2509.22751, is real but mis-scoped — it is an entity-linking/agent evaluator, not an index validator; a 2025 single-author preprint. Use only as a conceptual analogy — "prefer the framework whose Top-20% is robust across alternative profit definitions" — not as a canonical method. Dropped from the formal citation list.)*

---

## 3. Updated design guidance (new material)

### Citation hygiene — safe vs dropped
- **Now safe to cite (resolved this round, with DOI/venue):** Pfeifer–Carraway 2000; Twala–Jones–Hand 2008 (MIA); Mazziotta–Pareto 2018 (AMPI). All three carry verified DOIs.
- **Cite only as overlap/background, NOT as new finds:** Liu 2009 LTR survey and Wang 2018 LambdaLoss (LTR theme already covered) — keep the precision@top-quintile insight, not the algorithms; Venkatesan–Kumar 2004 (CLV canon) — confirm its venue/DOI before any direct citation.
- **Must stay dropped:** Random Indicator (Jolani & van Buuren, arXiv:2404.14534) — the *method* is real, but the *credit-scoring application is unverifiable*; cite only defensively if challenged. VB-Score (arXiv:2509.22751) — mis-scoped, analogy only.
- **Cite with corrected/loose numerals (overstated flags):** Chun–Iancu–Trichakis 2020 — drop the "$412M→$2.4B Delta" figure; IATA IFRS-15 — keep the 17–18% breakage benchmark, soften the per-airline 2024 liability dollars; Flagship Advisory — label as industry illustration, not primary evidence; CFPB — do not attribute a breakage % to it.

### Premium / charge-card economics — what it changes
- **Revenue mapping:** profit on the Premier *charge* card is interchange-on-spend-dominated with a *weaker* lending engine than a generic revolving card. Keep a strong net-spend term (`f5`, `f6`–`f10`, refunds `f7` netted) but **do not let raw `f5` be the top-20% sort key** — the Fed data show top spenders ≠ most profitable on interest-driven cards. *(Attribute the spend-centric framing to charge-card product logic, not to the revolving-credit sources.)*
- **Transactor handling:** go **segment-aware / piecewise** (So–Thomas–Seow–Mues). Charge-only/transactor members (low/absent `f1`, missing `f17`/`f18`) score on net spend × reward-cost efficiency; revolver/lender members (present `f1`/`f17`/`f18`) add an interest-revenue term discounted by risk (`f11`, `f3`). One linear revolve coefficient is wrong.
- **Wallet capture:** add relationship-breadth (`f19` supplementary, `f20` active cards) and category-breadth/diversity over `f6`–`f10` as share-of-wallet discriminators (Du–Kamakura–Mela; Jang–Prasad–Ratchford), built as a heuristic capture proxy inspired by Glady–Croux — high `f5` alone is NOT a high captured share.

### Rewards / benefit cost — setting the discount precisely
- **`f21` (redeemed):** realized cost, weight ≈ 1.
- **`f4` (balance):** contingent liability — cost ≈ `f4 × p_redeem × cost-per-point`. Anchor `p_redeem` with the audited **17–18% breakage** benchmark → a **redemption-discount band of ~80–90%** (sensitivity band, not a point estimate; premium charge members likely redeem at the high end).
- **Make the discount per-member, not flat:** modulate `p_redeem` by the **`f21/f4` (or `f21/(f4+f21)`) redemption ratio** and engagement (`f12` logins, `f22`/`f23` email). High ratio/engagement → near-full cost; dormant high-balance accumulators → breakage, cheaper than face value.
- **Use a concave/threshold transform on `f4`** (Hssaine et al.): small balances → near-zero expected cost; large balances near a redemption point → near-full cost.
- **Revenue-contingency (Chun et al.):** scale the `f4` penalty down where revenue features are high — the liability is "covered" by profit potential.
- **Attrition interaction:** pair high `f2` (cancellation calls) with high `f4` to lower expected cost further — attriting members often forfeit balances (CFPB).
- **`f13`–`f16` (benefit credits):** utilization-driven costs — enter on the cost side scaled by observed utilization; treat low utilization as a margin tailwind, not a flat entitlement charge.

### Label-free validation — concrete additions to our Top-20%-stability + Monte-Carlo plan
1. **Convergent validity / agreement-across-constructions** (Parisi–Nadler PNAS 2014; Jaffe–Nadler AISTATS 2015): build 3–5 semi-independent sub-scores, compute their agreement-covariance, take the leading eigenvector to rank/weight them — **report as corroboration, stating the shared-feature independence caveat.**
2. **Composite-indicator robustness** (OECD 2008; Saisana–Saltelli–Tarantola 2005): Monte-Carlo over normalization/weight/imputation choices + Sobol sensitivity → Top-20% membership-stability fraction and a "which choice moves the ranking" attribution. *Map the writeup onto the Handbook's 7 steps.*
3. **Bootstrap rank-stability** (challengeR / Maier-Hein): resample the 500K, recompute the Top-20% each time, report bootstrap retention frequency + Kendall-τ — our internal proxy for public-70% → hidden-30% generalization.
4. **Weak-supervision proxy label** (Ratner/Snorkel 2016): denoise business-rule LFs into a soft "high-profit" target used ONLY as a convergent-validity sanity check, never to train.
5. **Concentration / discrimination check** (Goix MV/EM 2016, simplified to **Lorenz/Gini** as our own in-house analogue): tie-breaker between two candidate frameworks before spending a submission — does the high-score region concentrate the "profitable minority" more tightly?

---

## 4. Net-new citations for the graded writeup

- **Twala, Jones & Hand 2008 (MIA, *Pattern Recognition Letters* 29(7):950–956, DOI 10.1016/j.patrec.2008.01.010)** — primary justification for encoding structured missingness (charge-only `f17`/`f18`, co-missing clusters) as signed terms instead of filling with 0.
- **Mazziotta & Pareto 2018 (AMPI, *Social Indicators Research* 136(3):967–976, DOI 10.1007/s11205-017-1577-5)** — citable non-compensatory aggregation (mean − CV penalty) and goalpost scaling for mixing heterogeneous drivers; A/B against weighted sum.
- **Saisana, Saltelli & Tarantola 2005 (*JRSS-A* 168(2):307–323, DOI 10.1111/j.1467-985X.2005.00350.x) + OECD/JRC Handbook 2008 (ISBN 978-92-64-04345-9)** — the textbook standard for validating a label-free composite index (Monte-Carlo + Sobol; 7-step backbone).
- **Glady & Croux 2009 (*Journal of Service Research* 11(3):219–231, DOI 10.1177/1094670508328983)** — academic cover for building a label-free wallet-capture term from internal data alone.
- **Gault, Llaguno & Menard 2012 (CAS E-Forum, Summer 2012) + IATA IFRS-15 17–18% breakage benchmark** — the contingent-liability identity (Points × Redemption-Rate × Cost-per-Point) and the audited breakage anchor for the `f4` discount.

---

## 5. Curated reading list (all included works, grouped K–N)

**K — Resolved primaries (new, on-theme):**
- Pfeifer & Carraway 2000 — *J. Interactive Marketing* 14(2):43–55, DOI 10.1002/(SICI)1520-6653(200021)14:2<43::AID-DIR4>3.0.CO;2-H.
- Twala, Jones & Hand 2008 (MIA) — *Pattern Recognition Letters* 29(7):950–956, DOI 10.1016/j.patrec.2008.01.010.
- Mazziotta & Pareto 2018 (AMPI) — *Social Indicators Research* 136(3):967–976, DOI 10.1007/s11205-017-1577-5.
- *(Overlap, background only:* Liu 2009 LTR survey, DOI 10.1561/1500000016; Wang et al. 2018 LambdaLoss, CIKM '18, DOI 10.1145/3269206.3271784. *Dropped:* Random Indicator, arXiv:2404.14534.*)*

**L — Premium / charge-card economics & share-of-wallet:**
- Du, Kamakura & Mela 2007 — *J. Marketing* 71(2):94–113, DOI 10.1509/jmkg.71.2.94.
- Glady & Croux 2009 — *J. Service Research* 11(3):219–231, DOI 10.1177/1094670508328983.
- Jang, Prasad & Ratchford 2016 — *Int. J. Research in Marketing* 33(1):123–139, DOI 10.1016/j.ijresmar.2015.06.005.
- So, Thomas, Seow & Mues 2014 — *Decision Support Systems* 59:143–151, DOI 10.1016/j.dss.2013.11.002.
- Adams, Bord & Katcher 2022 — Fed FEDS Notes, Sep 9 2022, DOI 10.17016/2380-7172.3100.
- Federal Reserve Board — Report to Congress on Credit Card Profitability (annual), federalreserve.gov/publications/credit-card-profitability.htm.
- Flagship Advisory Partners 2024 — "The Illusion of Premium Card Profitability" *(practitioner; illustration only)*.

**M — Rewards liability, breakage & benefit cost:**
- Gault, Llaguno & Menard 2012 — CAS E-Forum, Summer 2012 (casact.org).
- Chun, Iancu & Trichakis 2020 — *M&SOM* 22(2):223–259, DOI 10.1287/msom.2018.0748 *(drop the Delta $412M→$2.4B numeral)*.
- U.S. CFPB May 2024 — Credit Card Rewards Issue Spotlight (+ Circular 2024-07) *(qualitative; no breakage % attributable)*.
- Hssaine, Hu & Pike-Burke 2025 — arXiv:2506.03911.
- Matsui, Teramoto, Motohashi & Tsurumi 2025 — arXiv:2509.14508.
- IATA IAWG IFRS-15 Guidance 2018 — iata.org *(17–18% breakage confirmed; per-airline liability dollars loose)*.
- *J. Korean OR & Management Science Society* 2014 — KoreaScience JAKO201430756851448.

**N — Validating label-free / unsupervised scores:**
- Parisi, Strino, Nadler & Kluger 2014 (SML) — *PNAS* 111(4):1253–1258, DOI 10.1073/pnas.1219097111 (arXiv:1303.3257).
- Jaffe, Nadler & Kluger 2015 — AISTATS, PMLR v38:407–415 (arXiv:1407.7644).
- Saisana, Saltelli & Tarantola 2005 — *JRSS-A* 168(2):307–323, DOI 10.1111/j.1467-985X.2005.00350.x.
- Nardo et al. (OECD/JRC) 2008 — Handbook on Constructing Composite Indicators, ISBN 978-92-64-04345-9.
- Wiesenfarth, Reinke, Landman, Maier-Hein et al. 2021 (challengeR) — *Sci. Reports* 11:2369, DOI 10.1038/s41598-021-82017-6 (arXiv:1910.05121); companion Maier-Hein et al. 2018, *Nat. Commun.* 9:5217, DOI 10.1038/s41467-018-07619-7.
- Ratner, De Sa, Wu, Selsam & Ré 2016 (Data Programming / Snorkel) — NeurIPS 29:3567–3575 (arXiv:1605.07723).
- Goix 2016 (MV/EM curves) — ICML AD workshop, arXiv:1607.01152.
- *(Dropped: VB-Score, arXiv:2509.22751 — analogy only.)*

---

## 6. Honest gaps remaining

- **The credit-scoring use of Random Indicator (MNAR imputation) is still unverifiable** — the method exists, but no source ties it to credit scoring. Unresolved; we deliberately do not adopt it, preferring MIA flag-encoding.
- **Three numerals remain soft/unconfirmed:** the AMPI `[70,130]` goalpost range (not independently re-echoed this pass — verify against the Springer PDF before quoting verbatim); the Chun et al. "Delta $412M→$2.4B" jump (conflicts with public filings — drop); and the IATA per-airline 2024 liability dollars (drift from 10-Ks — the 17–18% breakage benchmark is the only IATA figure we should quote firmly).
- **Venkatesan–Kumar 2004 was not re-fetched** this round; its CLV-canon overlap framing is accepted conservatively, but confirm venue/DOI before any direct citation.
- **No per-member redemption history exists** (single 12-month snapshot), so the actuarial redemption-triangle machinery (Gault et al., chain-ladder) cannot be run; the `f21/f4` ratio is our defensible proxy, explicitly an extrapolation, not the paper's procedure.
- **The conditional-independence assumption underlying the spectral methods (Parisi, Jaffe) and Snorkel is violated** by our shared-feature design — these stay triangulating/corroborating signals, never point estimates of accuracy. This is a structural limit of the no-label setting, not a search gap.
- **Tooling reachability:** Semantic Scholar was unavailable (HTTP 402) and arXiv returned essentially nothing on-topic for premium-card/share-of-wallet economics (only crypto-wallet and fraud-detection noise) — that literature legitimately lives in marketing-science journals, regulatory data, and practitioner P&L work, all reached via WebSearch. Full texts were not opened for every kept work; verifiability is per-item (author + year + venue + DOI confirmed).
- **Diminishing returns:** YES. Across rounds 1–3 the four families now have redundant, mutually-reinforcing primary coverage (missingness-as-signal, non-compensatory aggregation, charge-card profit physics, label-free SOW, contingent-liability rewards costing, and a four-method label-free validation protocol). Further search is unlikely to change the framework's structure — remaining effort is better spent **implementing and A/B-testing** (AMPI vs weighted sum; the per-member `f4` discount; the bootstrap + Monte-Carlo + spectral validation suite) than scouting more literature. Only re-open the search if a specific reviewer challenge requires a numeral we flagged as soft.