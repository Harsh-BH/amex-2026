# Bibliography — Research Papers Read (R1)

_Provenance log of every source consulted for the profitability framework. Status legend:
**✅ verified** (adversarially checked + exists) · **🔎 spot-checked** (I confirmed via arXiv `get_paper`
or WebSearch) · **⚠ overstated** (real, but the implication overreaches — use narrowly) · **➖ screened**
(read in search results, not carried). Full prose: `reports/literature-review-r1-profitability.md`
(round-1 report + round-2 addendum); design use: [[research-findings]]._

## Counts at a glance
- **Total verified & cited: ~70 distinct works** (Round 1: 18 · Round 2: 30 · Round 3: ~22; non-overlapping).
- **Screening effort:** 3 workflows, **31 agents, 399 tool calls**, several hundred hits skimmed.
- **I personally verified 9**: `get_paper` on 2009.04536, 1703.02596, 1403.6531, 2103.01907,
  2008.08662, 2402.04103, 1303.3257, 1605.07723; WebSearch on Gupta-Lehmann-Stuart (2004).
- **Research CLOSED after round 3** (own verdict: diminishing returns → build next).
- **Excluded as unverifiable (7):** see §Excluded below — do NOT cite as verified.
- **Semantic Scholar: PERMANENTLY UNAVAILABLE** — the Smithery-hosted `hamid-vakilzadeh/mcpsemanticscholar`
  server returns **HTTP 402 (Payment Required)**; `/mcp` re-auth confirmed it needs a paid plan. Do NOT
  retry. All research runs on **arXiv MCP + WebSearch**; canon/journal works reached via WebSearch + DOI.

---

## ROUND 1 — verified & cited (18)

### arXiv (15)
| arXiv id | Title | Status | Why it matters |
|---|---|---|---|
| 2506.22711 | Potential CLV in Financial Institutions (PCLV) | ✅ | `margin × retention` skeleton |
| 1912.07753 | A Deep Probabilistic Model for CLV (ZILN) | ✅ | log/winsorize tails; Gini + decile validation |
| 2304.03038 | Modelling CLV in retail banking | ✅ | 3.2× top-decile lift = separation template |
| 2507.08860 | e-Profits | ✅ | per-customer `revenue×retention−cost`; profit eval reshapes rankings |
| 2401.12323 | Bank Business Models, Size & Profitability | ✅ | component-attribution (bank-level) |
| 1205.1609 | CSHURI — Segmentation & Transaction Profitability | ✅ | margin-weight behaviors |
| 1703.02596 | CLV Prediction Using Embeddings (ASOS) | 🔎 | handcrafted features = strong baseline |
| 2506.11037 | GRePO-LTV (WeChat) | ✅ | value concentrated in tail |
| 1506.05376 | Optimal limits for transacting cards | ✅ | closed-form, label-free profit |
| 2305.11375 | Weighing Anchor on Credit Card Debt | ✅ | revolving = durable revenue |
| 2506.03911 | Fair Points-Based Rewards | ⚠ | reward = realized cost on redemption (program-design caveat) |
| 2203.06641 | Profit in Recommenders | ✅ | profit-weight lifts precision + profit |
| 2009.04536 | Credit→Profit Scoring (P2P) | 🔎 | two-stage risk discount |
| 1403.6531 | Credit acceptance strategy (Przanowski) | 🔎 | cutoffs = tail-sensitive top-k |
| 2103.01907 | Fairness in Credit Scoring | 🔎 ⚠ | "profit > accuracy" framing only — NOT an EMP source |

### OR/marketing journals (3 — DOI-cited, re-verify before writeup)
| Source | Title | Status |
|---|---|---|
| EJOR S0377221712006078 (2013) | Risk-Adjusted Revenue (RAR) | ⚠ multiplicative risk discount (mechanism = discount-rate) |
| DSS 2014, eprints.soton.ac.uk/359696 | Transactor/Revolver scorecard | ✅ segment-aware revenue formulas |
| EJOR 10.1016/j.ejor.2014.04.001 (2014) | Expected Maximum Profit (EMP) | ✅ `loss = LGD×EAD×PD`; ranking ≠ calibration |

---

## ROUND 2 (gap-fill) — verified & cited (30)

### F. CLV / Customer-Equity Canon (6)
- **Fader, Hardie & Lee (2005)** "RFM and CLV: Iso-Value Curves" — *JMR* 42(4):415–430, DOI 10.1509/jmkr.2005.42.4.415 — ✅ label-free RFM→value; log/rank-transform, don't sum. *(⚠ "value is multiplicative" = motivation, not proof.)*
- **Gupta, Lehmann & Stuart (2004)** "Valuing Customers" — *JMR* 41(1):7–18, DOI 10.1509/jmkr.41.1.7.25084 — 🔎 ✅ retention 1%→5% value vs margin 1% (elasticity 3–7) → weight risk/retention high. *(Firm-value elasticities; per-member = heuristic.)*
- **Berger & Nasr (1998)** "CLV: Marketing Models and Applications" — *J. Interactive Mktg* 12(1):17–30 — ✅ canonical `(rev−cost)×retention/(1+d)` template.
- **Schmittlein, Morrison & Colombo (1987)** "Counting Your Customers" — *Mgmt Science* 33(1):1–24, DOI 10.1287/mnsc.33.1.1 — ✅ Pareto/NBD; activity-as-value (cite, can't fit — no timestamps).
- **Fader, Hardie & Lee (2005)** "Counting Your Customers the Easy Way (BG/NBD)" — *Mktg Science* 24(2):275–284 — ✅ split frequency from monetary. *(⚠ decomposition needs BG/NBD + Gamma-Gamma.)*
- **Rust, Lemon & Zeithaml (2004)** "Return on Marketing / Customer Equity" — *J. Marketing* 68(1):109–127 — ✅ customer equity = Σ CLV; relationship-equity vocabulary.

### G. Learning to Rank & Top-k (5) — *finding: LTR trainers need labels → inapplicable as trainers; reuse eval framing + label-free fusion*
- **Cormack, Clarke & Büttcher (2009)** "Reciprocal Rank Fusion" — SIGIR 2009 pp.758–759, DOI 10.1145/1571941.1572114 — ✅ **label-free, scale-free, top-heavy fusion of our P&L sub-rankings** (key mechanism).
- **Taylor, Guiver, Robertson & Minka (2008)** "SoftRank" — WSDM 2008 pp.77–86 — ✅ smoothed-rank → expected top-20% membership = our stability test.
- **Burges (2010)** "RankNet→LambdaRank→LambdaMART overview" — MSR-TR-2010-82 — ✅ "errors near the top matter most" → calibrate at the 80th-pct cutoff.
- **Burges et al. (2005)** "RankNet" — ICML 2005 — ✅ legitimizes monotone sorted scoring (needs labels as trainer).
- **Cao et al. (2007)** "ListNet" — ICML 2007 — ✅ softmax → top-k inclusion probabilities (confidence diagnostic).

### H. Composite Indicators & MCDA (6) — *our framework IS a composite indicator*
- **OECD/JRC (2008)** "Handbook on Constructing Composite Indicators" — JRC47008, ISBN 978-92-64-04345-9 — ✅ **adopt the 7-step pipeline as the Framework-sheet skeleton**.
- **Greco, Ishizaka, Tasiou & Torrisi (2019)** — *Social Indicators Research* 141(1):61–94 — ✅ objective weighting + partial-compensation; weights ≠ importance under non-linear aggregation.
- **Diakoulaki, Mavrotas & Papayannakis (1995)** "CRITIC" — *Computers & OR* 22(7):763–770 — ✅ **correlation-aware weights → deflate collinear f5–f10**.
- **Karagiannis & Karagiannis (2020)** "Shannon-entropy composites" — *Socio-Econ. Planning Sci.* 70:100701 — ✅ objective entropy-weight baseline.
- **Hwang & Yoon (1981)** "TOPSIS" — Springer LNEMS 186 — ✅ rank by closeness to ideal-profitable profile (C∈[0,1]).
- **Saisana, Saltelli & Tarantola (2005)** — *JRSS-A* 168(2):307–323 — ✅ **Monte-Carlo sensitivity = our no-label validation** (top-20% stability).

### I. Segmentation & Financial Feature Engineering (7 net-new) — *recovered Theme E*
- **Hughes (1994)** "Strategic Database Marketing (RFM 5×5×5)" — McGraw-Hill — ✅ quintile RFM origin.
- **Bult & Wansbeek (1995)** — *Mktg Science* 14(4):378–394 — ✅ first peer-reviewed RFM; rank/quintile composite auto-normalizes scale mismatch.
- **WRFM/eRFM** — *Procedia CS* 3 (2011), DOI 10.1016/j.procs.2010.12.011 — ⚠ business-reasoned weighted RFM (conflated entry — use the *idea*).
- **John, Shobayo & Ogunleye (2023)** — *Analytics* 2(4):809–823 (arXiv:2402.04103) — 🔎 ✅ GMM > k-means on skewed spend (Silhouette 0.80); pseudo-ground-truth recipe.
- **Aliyev et al. (2020)** "Segmenting Bank Customers via RFM + Unsupervised ML" — arXiv:2008.08662 — 🔎 ✅ closest-domain (bank) precedent; value-tier profiling.
- **Kanter & Veeramachaneni (2015)** "Deep Feature Synthesis" — IEEE DSAA 2015 — ✅ ratio/aggregation primitive vocabulary (single-table only).
- **Wedge et al. (2017)** "False Positives in Fraud Prediction" — arXiv:1710.07709 — ✅ customer-relative aggregate features (card domain).
- _(Fader-Hardie-Lee 2005 iso-value cross-listed from Theme F.)_

### J. Behavioral Scoring & Attrition (6) — *cost/risk side*
- **Thomas, Edelman & Crook (2002/2017)** "Credit Scoring and Its Applications" — SIAM — ✅ defines behavioral scoring + additive WOE scorecard form.
- **Stepanova & Thomas (2002)** "Survival Analysis for Personal Loan Data" — *Operations Research* 50(2):277–289 — ✅ Cox PH discount + survival coarse-classification binning.
- **Van den Poel & Lariviere (2004)** "Customer attrition via proportional hazards" — *EJOR* 157(1):196–217 — ✅ attrition-hazard form for the retention discount.
- **Verbraken, Verbeke & Baesens (2013)** "EMP/EMPC for churn" — *IEEE TKDE* 25(5):961–973 — ✅ profit-fraction objective; cost-benefit weighting.
- **Bahnsen, Aouada & Ottersten (2015)** "Example-Dependent Cost-Sensitive Trees" — *ESWA* 42(19):6609–6619 (arXiv:1505.04637) — ✅ per-example costs → revenue × distress interaction.
- **So & Thomas (2011)** "Profitability of credit cards by MDP" — *EJOR* 212(1):123–130 — ✅ credit-card profit-MDP licenses revenue × risk-discount.

---

## Excluded as UNVERIFIABLE this round (do NOT cite as verified)
- Liu (2009) LTR survey (FnT IR 3(3)); Wang et al. (2018) LambdaLoss (CIKM); Precision@k textbook definition — canonical but not independently confirmed.
- Pfeifer & Carraway (2000) Markov CLV; Venkatesan & Kumar (2004) CLV selection — real & relevant, verify separately before use.
- Mazziotta-Pareto (MPI/AMPI) primary source — none verified.
- **Dropped (mis-attribution):** arXiv:1707.01166 submodular rank aggregation (wrong authors in scout output).

## Screened in Round 1 but NOT carried
2105.14198 (Bangladesh bank profitability), 2211.09176 (auto-loan risk), 2508.01851 (SHAP), 2102.04721 (imbalanced scoring), 1805.03581 (sharing-economy loyalty).

---

## ROUND 3 (targeted) — verified & cited (~22)

### K. Resolved flagged primaries (3 new)
- **Pfeifer & Carraway (2000)** "Modeling Customer Relationships as Markov Chains" — *J. Interactive Mktg* 14(2):43–55, DOI 10.1002/(SICI)1520-6653(200021)14:2<43::AID-DIR4>3.0.CO;2-H — ✅ resolved. Markov-state framing for behavioral archetypes (can't fit — no timestamps).
- **Twala, Jones & Hand (2008)** "MIA — missing data in decision trees" — *Pattern Recognition Letters* 29(7):950–956, DOI 10.1016/j.patrec.2008.01.010 — ✅ resolved. **Primary cite for missingness-as-signal** (don't fill-0).
- **Mazziotta & Pareto (2018)** "AMPI" — *Social Indicators Research* 136(3):967–976, DOI 10.1007/s11205-017-1577-5 — ✅ resolved. Non-compensatory aggregator (mean − CV penalty); A/B vs weighted sum.
- _Overlap (real, not new): Liu 2009 LTR survey; Wang 2018 LambdaLoss; Venkatesan-Kumar 2004 (confirm venue before citing). **DROPPED:** Random Indicator MNAR (arXiv:2404.14534) — credit-scoring framing unverifiable._

### L. Premium / charge-card economics & share-of-wallet (7)
- **Du, Kamakura & Mela (2007)** "Size and Share of Customer Wallet" — *J. Marketing* 71(2):94–113, DOI 10.1509/jmkg.71.2.94 — ✅ size vs share of wallet; high `f5` ≠ dominant captured share.
- **Glady & Croux (2009)** "Predicting Customer Wallet Without Survey Data" — *J. Service Research* 11(3):219–231, DOI 10.1177/1094670508328983 — ✅ **label-free SOW** template (analogy for a wallet-capture term).
- **Jang, Prasad & Ratchford (2016)** — *Int. J. Research in Mktg* 33(1):123–139, DOI 10.1016/j.ijresmar.2015.06.005 — ✅ category-breadth/spend-diversity term.
- **So, Thomas, Seow & Mues (2014)** "Transactor/revolver scorecard for credit & pricing" — *Decision Support Systems* 59:143–151, DOI 10.1016/j.dss.2013.11.002 — ✅ segment-aware (piecewise) profit, not one linear revolve coefficient. *(Distinct from round-1 So-Thomas.)*
- **Adams, Bord & Katcher (2022)** "Credit Card Profitability" — Fed FEDS Note, DOI 10.17016/2380-7172.3100 — ✅ **top spenders ≠ most profitable** → don't rank by raw `f5`. *(Revolving-portfolio source; charge-card framing is our inference.)*
- **Federal Reserve** "Report to Congress on Credit Card Profitability" (annual) — ✅ portfolio ROA sanity-check anchor.
- **Flagship Advisory Partners (2024)** "The Illusion of Premium Card Profitability" — ⚠ practitioner; points+credits eat 60%+ of revenue (illustration only).

### M. Rewards liability, breakage & benefit-cost (6)
- **Gault, Llaguno & Menard (2012)** — CAS E-Forum — ✅ **Cost = Points × Redemption-Rate × Cost-per-Point**; breakage = 1−redemption.
- **Chun, Iancu & Trichakis (2020)** — *M&SOM* 22(2):223–259, DOI 10.1287/msom.2018.0748 — ⚠ revenue-contingent liability (drop the "Delta $412M→$2.4B" numeral).
- **U.S. CFPB (May 2024)** "Credit Card Rewards" Issue Spotlight (+ Circular 2024-07) — ✅ breakage/forfeiture directional support (no breakage % attributable to it).
- **Hssaine, Hu & Pike-Burke (2025)** — arXiv:2506.03911 — ✅ threshold-driven redemption → concave transform on `f4`. *(Also round-2 — not double-counted.)*
- **Matsui et al. (2025)** — arXiv:2509.14508 — ✅ redemption propensity predictable from engagement → modulate `f4` cost per member.
- **IATA IAWG IFRS-15 Guidance (2018)** — iata.org — ⚠ **17–18% breakage benchmark confirmed**; per-airline 2024 liability dollars loose.
- _J. Korean OR&MS (2014), JAKO201430756851448 — redemption-RFM supports `f21/f4` propensity proxy._

### N. Validating label-free scores (6)
- **Parisi, Strino, Nadler & Kluger (2014)** "Spectral Meta-Learner" — *PNAS* 111(4):1253–1258 (arXiv:1303.3257) — 🔎 ✅ rank/weight sub-scores by agreement-covariance eigenvector, no labels.
- **Jaffe, Nadler & Kluger (2015)** — AISTATS PMLR v38:407–415 (arXiv:1407.7644) — ✅ estimate per-predictor accuracy unlabeled.
- **Saisana, Saltelli & Tarantola (2005)** — *JRSS-A* 168(2):307–323 — ✅ Monte-Carlo + Sobol robustness *(also round-2)*.
- **Nardo et al. OECD/JRC Handbook (2008)** — ISBN 978-92-64-04345-9 — ✅ 7-step backbone *(also round-2)*.
- **Wiesenfarth et al. challengeR (2021)** — *Sci. Reports* 11:2369 (arXiv:1910.05121) + Maier-Hein et al. (2018) *Nat. Commun.* 9:5217 — ✅ bootstrap rank-stability protocol.
- **Ratner, De Sa, Wu, Selsam & Ré (2016)** "Data Programming/Snorkel" — NeurIPS 29:3567–3575 (arXiv:1605.07723) — 🔎 ✅ weak-supervision proxy label (sanity-check ONLY).
- **Goix (2016)** "MV/EM curves" — ICML AD workshop (arXiv:1607.01152) — ✅ label-free framework tie-breaker (Lorenz/Gini = our in-house analogue).
- _DROPPED: VB-Score (arXiv:2509.22751) — mis-scoped, analogy only._

## Excluded across rounds (do NOT cite as verified)
Random Indicator credit-scoring framing (2404.14534) · VB-Score (2509.22751) · Pfeifer-Carraway-overlap items as "new" · Liu 2009 / Wang 2018 / Venkatesan-Kumar 2004 (overlap/confirm-first). Soft numerals to re-source: AMPI [70,130] goalpost; Chun "Delta $412M→$2.4B"; IATA per-airline 2024 dollars (17–18% breakage is firm).
