# Methodology Redesign: Optimal-Experimental-Design Reformulation of the Leaderboard-Inversion Pipeline

_Research-grade review and redesign, 2026-07-04 (late night). Reviewer persona: principal
researcher in Bayesian experimental design / weak supervision / inverse problems. Everything
here is anchored to this project's own 30 paid measurements — the strongest evidence base
available — rather than to generic theory. Citations were drafted from memory and are being
verified by a parallel literature pass; an annotated table will be appended as Annex A._

---

## 1. Executive summary

The current pipeline is an unusually disciplined instance of the right *idea* — treat the
leaderboard as a measurement channel, invert it — implemented with four ad-hoc components
where formal machinery exists: (i) a **level-set ensemble masquerading as a posterior**,
(ii) **marginal votes where covariance is the decision-relevant object**, (iii) **an
axe-list experiment scheduler where expected-information-gain design is computable**, and
(iv) **three separate patches (λ-shrink, percentile-edge model, trust-region+veto) that all
approximate one missing thing: a mis-specification-aware generalized posterior.**

The redesign keeps the interpretable scoring equation and the pre-registration discipline
(both are assets) and replaces the inference/design core:

1. **Generalized (Gibbs) posterior with learned temperature η** over weights θ — fixes the
   measured calibration failures (three consecutive bottom-quartile self-reads; persistent
   +0.008–0.015 E[LB] optimism) at near-zero compute cost by *reweighting the existing
   ensemble*.
2. **Explicit displacement model δ** (spike-and-slab over cohorts) for the out-of-family
   residue the family provably cannot express (best in-family RMSE 0.003–0.005 vs measured
   channel noise σ ≈ 0.001). Probes become formal likelihood updates on δ, not side-notes.
3. **Covariance-aware probe design ("eigen-probes")**: choose swap pools to maximize the
   posterior *variance of the queried count* — computable in closed form from the ensemble
   mask matrix — instead of testing named axes. Retrospectively, ~half of the archive's 30
   reads were spent on near-duplicate queries (mutual top-set overlaps 0.975–0.995); a
   variance-targeting designer extracts the same information in roughly half the reads.
4. **Decision-theoretic scheduling**: greedy EIG probes while information is cheap, Thompson
   /knowledge-gradient exploits when it is not, and a P(max ≥ target) portfolio rule for
   final submissions (best-score-counts makes downside asymmetric).
5. **A simulation harness** (synthetic truths drawn from the current posterior + measured δ
   densities) so policies are compared by Monte-Carlo regret *before* paying for reads —
   the single highest-leverage missing tool.

Honest ceiling statement: none of this repeals the identifiability limits of §4. The
redesign's value is (a) calibrated uncertainty (replacing patches with one principled knob),
(b) ~1.5–2× information per read, (c) fewer wasted submissions. On this competition's
remaining budget it is worth an estimated +0.002–0.006 of realized score versus the current
policy; had it governed from read #1, the evidence says ~15–18 reads would have bought what
30 did.

## 2. Literature review (mapped to this problem)

**Measurement model.** Each submission is a *counting query*: the response is a noisy
linear functional ⟨1_S, t⟩ of the hidden membership vector t (top-20% indicator). This is
the pooled-data / quantitative-group-testing observation model, and in the dense regime
(k = 0.2n) member-level identification needs Θ(n/log n) queries — tens of thousands, not
tens (cf. one-bit/aggregate compressed sensing, Plan & Vershynin 2013 CPAM). All practical
inference therefore flows through a low-dimensional structural prior. This is also exactly
learning-from-label-proportions with adversarially few, adaptively chosen bags (Quadrianto
et al. JMLR 2009; hardness for linear thresholds: Brahmbhatt–Saket–Raghuveer NeurIPS 2023);
the LLP literature's design result that *curated bags dominate random ones* (PriorBoost:
Javanmard–Fahrbach–Mirrokni 2024) is the license for designed swap probes.

**Inference under mis-specification.** When the model class cannot interpolate the data
(ours cannot: RMSE floor ≈ 3–5σ), the Bayesian posterior concentrates on a pseudo-truth and
its credible sets lose calibration (White 1982 Econometrica; Grünwald & van Ommen 2017
Bayesian Analysis). The remedy is the generalized/Gibbs posterior π_η(θ) ∝ π₀(θ)
exp(−η·L(θ)) with η tuned for calibration (Bissiri–Holmes–Walker JRSS-B 2016; SafeBayes;
optimization-centric generalized VI: Knoblauch–Jewson–Damoulas JMLR 2022). Likelihood-free
sampling for our simulator-defined L: ABC-SMC (Toni et al. 2009 J R Soc Interface; adaptive
version Del Moral–Doucet–Jasra 2012 Stat Comput).

**Experimental design.** Expected-information-gain design goes back to Lindley (1956 Ann.
Math. Stat.) and Chaloner–Verdinelli (1995 Statistical Science); the modern computational
treatment is Rainforth–Foster–Ivanova–Bickford-Smith (2024 Statistical Science), with
amortized sequential variants (Deep Adaptive Design, Foster et al. ICML 2021; implicit-
likelihood variant Ivanova et al. NeurIPS 2021) — the amortized machinery is overkill here
because our design space (swap pools) admits closed-form variance computations; the greedy
policy inherits near-optimality from adaptive submodularity (Golovin & Krause JAIR 2011).
The batch-diversity insight — score candidate queries by *joint* mutual information, not
sums of marginal entropies — is BatchBALD (Kirsch–van Amersfoort–Gal NeurIPS 2019),
transplanted here from label-querying to count-querying.

**Exploration/exploitation and endgame.** Thompson sampling as the exploit-with-free-
information policy (Russo et al., FnT ML 2018); knowledge-gradient for explicit one-step
value-of-information comparisons (Frazier–Powell–Dayanik 2008 SIAM J. Control Opt.);
final-slot portfolio selection maximizing P(max ≥ bar) (Hunter–Vielma–Zaman, DFS portfolio
construction; Aldous 2021 Amer. Statistician on winner-take-all extremization).

**Optimizer layer.** Population methods that reuse evaluations (CMA-ES, Hansen 2016
tutorial; cross-entropy method, Rubinstein 1999) dominate independent multi-start DE for
posterior-shaped exploration. Differentiable sorting/top-k surrogates (Cuturi–Teboul–Vert
NeurIPS 2019; Blondel et al. ICML 2020; OT top-k, Xie et al. NeurIPS 2020; monotonic
sorting networks, Petersen et al. ICLR 2022) smooth the discontinuous top-K objective for
fast local moves — used as *proposal machinery only*, with exact top-K evaluation as the
accept step (smoothing bias near the cutoff is a known artifact).

**Validation.** Distribution-free predictive intervals from few residuals: conformal
prediction (Angelopoulos & Bates 2023 FnT ML). Signal validity under selection: our own
measured Goodhart event (a 7/7 observationally-validated signal failing when optimized
against, v43) is the textbook caution the design must encode — signals earn *passive*
(veto/tie-break) roles from retrodiction, never *active* (selection) roles without a paid
scale-test.

## 3. Mathematical critique of the current pipeline

Setup: t ∈ {0,1}^N, N = 500,000, Σt = K = 100,000. Read i: y_i = ⟨1_{S_i}, t⟩/K + ε_i,
σ(ε) ≈ 0.001 (measured, A42: 70/30 thinning of exact integer counts/70,000). Model:
t ≈ topK(g_θ), θ ∈ R^15. Loss L(θ) = Σ w_i (y_i − φ_i(θ))², φ_i(θ) = ⟨1_{S_i}, topK(g_θ)⟩/K.

**(C1) The "posterior" is a level set, not a posterior.** Keeping the 25/48 runs with
RMSE ≤ 1.5×min with *uniform weights* approximates {θ : L(θ) ≤ c}, i.e. a confidence
*region boundary*, not a density: (i) no within-set likelihood weighting; (ii) c is
arbitrary; (iii) multi-start hit rates reflect optimizer basin sizes, not posterior mass.
Predictable consequences, all *measured*: self-reads landing in the predictive bottom
quartile three times running (joint p ≈ 2% if calibrated); persistent E[LB] optimism
(+0.008–0.015 across refits 23→30); the need for the λ-shrink and "percentile-edge"
patches. **Fix (cheap):** importance-reweight the existing kept set by
w(θ) ∝ exp(−η Σ_i (y_i − φ_i(θ))²/(2σ_tot²)), with σ_tot² = σ² + τ² and (η, τ) chosen so
the 8 pre-registered probe outcomes achieve nominal coverage (SafeBayes-style grid on two
scalars). This costs minutes and immediately repairs vote weighting, E[LB] prediction, and
candidate pricing.

**(C2) Mis-specification is load-bearing and unmodeled.** L_min corresponds to residuals
3–5× channel noise; under White (1982) the fit concentrates on a pseudo-truth and the
missing structure is *systematic*. This project already measures the missing part — as
probe outcomes (engagement pool: parity; supp pool: −0.41; pu-top pool: −0.29; f3-elite:
≈ −0.6 in-rate ≈ 0; nbd level: ≈ right) — but stores them as narrative, not as likelihood.
**Fix:** explicit displacement layer: t = topK(g_θ) ⊕ δ, with δ constrained by cohort-level
spike-slab rates π_c (cohorts = the probeable partition: missingness cells × segment ×
boundary bands). Each swap probe is then a *direct* binomial observation of π over its
pool. The predictive for any candidate becomes Var_read = J-term(θ) + Σ_pools π-term(δ) —
which is exactly what the λ patch was approximating by hand.

**(C3) Marginal votes discard the decision-relevant covariance.** The value of querying a
pool Q (swap-in q⁺, swap-out q⁻) is, to Gaussian approximation,
EIG(Q) = ½ log(1 + Var_post(⟨s_Q, t⟩)/σ²), s_Q = (1_{q⁺} − 1_{q⁻})/K.
Var_post(⟨s_Q, t⟩) = s_Qᵀ Σ_t s_Q where Σ_t is the member co-membership covariance —
available in low rank from the ensemble mask matrix M (25×N): Σ_t ≈ MᵀWM − μμᵀ. Ranking
members by *marginal* vote and swapping the extremes maximizes Σ_j |μ_j − ½| — the wrong
functional; high-EIG pools are *covariance-coherent* (the BatchBALD lesson). Retrospective
audit: the archive's recent queries were mutually redundant (top-set overlaps 0.975–0.995;
several feature directions with capture-range ≈ 0 across all 30 reads) — i.e., the design
repeatedly re-measured the same dominant mode while leaving whole directions at zero
excitation. **Fix:** the eigen-probe designer of §8.

**(C4) Response-magnitude weighting (OBS_POW = 2) has no noise justification.** All reads
share σ; precision weighting is uniform. Upweighting high-scoring reads warps the
*likelihood* to express a *decision* preference (boundary relevance near our candidates).
The correct decomposition: uniform likelihood; decision-focus lives in the utility
(posterior predictive of candidate composition), not in the data weights. Empirically
testable via LOO; expected effect: better identification of the *form* (the early, diverse
reads are the most form-discriminating and are currently down-weighted ~4×).

**(C5) Evaluation waste in the optimizer.** 48 independent DE runs ≈ 5×10⁵ evaluations,
of which only 25 terminal points are retained. SMC/CE-method style populations reuse the
entire evaluation history as weighted particles; a differentiable top-K surrogate
(entropic-OT soft top-k) provides cheap local moves inside basins. Expected ~5–10× cost
reduction per refit — which converts "refit ≈ 3 h, batch the reads" into "update ≈
minutes, sequential Bayesian updating after every read" (a qualitative workflow change:
the 15-minute LB cadence stops being wasted).

**(C6) Experiments scheduled by named hypotheses, not by information.** The axe-list had
scientific virtues (interpretability, pre-registration) and paid measurable costs: reads
spent on near-determined questions while f19/f20/f23 sat at zero excitation for 28 reads;
two of this week's three bench probes (v40, v43) were *predictable losers under the
already-available graded signal* — justified as hypothesis-closures, but an EIG scheduler
would have bought comparable entropy reduction from pools with upside. **Fix:** §8's
scheduler with the free-option constraint (bench reads are pure EIG; primary reads must
satisfy the two-leaderboard replacement guard).

**(C7) Three patches, one cause.** λ-shrink (echo discount), the "percentile-edge"
selection model, and the pu-veto are all local corrections for overconfident member-level
beliefs. The Gibbs-η + δ-layer posterior subsumes all three: echo *is* the uniform-weight
level-set bias; the edge model *is* the missing predictive dispersion; the veto *is* a
crude spike-slab update. Consolidation removes ~200 lines of heuristics and their tuning
constants.

## 4. Identifiability analysis (what 30 reads can and cannot determine)

- **Member level:** infeasible by channel capacity: H(t) ≈ N·H(0.2) ≈ 3.6×10⁵ bits vs
  ≤ ~13 bits/read nominal (integer counts spanning a few thousand values), and far less
  effectively (responses cluster in [0.90, 0.92]).
- **Parameter level:** the empirical Jacobian (finite differences of implied readings along
  feature directions — equivalently the capture-range audit) shows 6–8 well-excited
  directions of 15; f19/f20/f23-type combinations have near-zero rows across the entire
  archive: *no estimator can identify them from this design*, which the seed-instability
  of those coefficients in refits 26–30 corroborates. Conclusion: the fitted family's
  identified content ≈ the 4 sign-stable pillars + 2–4 soft ratios; the rest is prior.
- **Displacement level:** exactly five pool-aggregates of δ are measured (f3-elite ≈ 0
  in-rate; nbd level ≈ right; engagement 1,741-pool ≈ parity; supp 1,200-pool ≈ −0.41;
  pu-top 2,500-pool ≈ −0.29 vs weakest incumbents). δ elsewhere is untouched prior mass —
  up to ~7×10³ members' worth (LP bound) in never-probed territory.
- **Noise floor of conclusions:** every probe differential carries ±15–26 members (1σ) of
  70/30 thinning noise; the λ calibration points are therefore 1–2σ statements — another
  reason to replace point-λ with posterior dispersion.

## 5–7. Improved architecture, optimizer, posterior inference

**Architecture (replaces steps 2–3; keeps the scoring equation and rules):**

    Layer 0  scoring equation g_θ (unchanged; interpretability is a graded asset)
    Layer 1  generalized posterior over θ: π_η ∝ exp(−η·Σ(y_i − φ_i)²/2σ_tot²)
             η, τ calibrated on the 8 pre-registered probe residuals (coverage matching)
    Layer 2  displacement δ over cohorts: spike-slab π_c; probe outcomes = direct updates
    Layer 3  predictive for any candidate S: E[y|S], Var[y|S] from (θ, δ) jointly
             → replaces λ, percentile-edge, and hand-built boxes (conformal check on top)

**Optimizer:** retrofit path (1 day): keep DE populations but (a) retain *all* evaluated
points, (b) importance-weight by the Layer-1 likelihood, (c) resample-move with CMA-ES
proposals (SMC structure). Optional accelerator: soft-top-K surrogate for within-basin
gradient moves (entropic OT, ε tuned so surrogate-vs-exact disagreement < 100 members at
the cutoff; always accept on exact φ).

**Posterior inference quality targets** (testable): (i) predictive coverage of the 8
historical probes ≥ 7/8 at 80% intervals after η-calibration; (ii) E[LB] anchor bias for
banked sets within ±0.002 (currently +0.002 on v35/v37L anchors but −0.01 to −0.03 on far
candidates); (iii) vote-band truth-rates consistent with the five measured pool aggregates.

## 8. Improved experiment design (the eigen-probe designer)

Given ensemble masks M (kept calibrations × members) with Layer-1 weights w:

1. μ = wᵀM (member inclusion probabilities), restrict to the active band B =
   {j : ζ < μ_j < 1−ζ} ∪ {measured-δ cohorts} (≈ 30–60K members).
2. Low-rank covariance on B: Σ_B = (M_B − μ_B)ᵀ W (M_B − μ_B) (rank ≤ #kept).
3. Top eigenvectors v₁, v₂, … of Σ_B. **Eigen-probe k:** swap-in = top-m positive
   components of v_k outside the current set, swap-out = top-m negative components inside
   it (whale/f3/f11 guards as usual), m sized so the *predicted count s.d.* ≥ 5σ (so one
   read resolves the mode): m ≈ 1–3K typically.
4. EIG(probe) ≈ ½log(1 + s_Qᵀ Σ_t s_Q/σ_tot²); schedule highest-EIG first; after each
   read, rank-1 downdate and repeat (greedy, near-optimal by adaptive submodularity).
5. Null-space rider blocks: append ≤ 300-member blocks along zero-excitation directions
   (from the Jacobian audit) — they cost little variance budget and buy first-ever
   excitation of dead directions.

This tool is implementable *tonight* on existing artifacts (mask matrices + guards + the
established swap-build machinery); it emits the same pre-registered box arithmetic as every
prior probe.

## 9. Improved update policy

Replace "trust region + veto by decree" with decision theory on the calibrated predictive:

- **Bench (free option):** admit any read with EIG above a floor; prefer eigen-probes.
- **Primary (two-LB replacement risk):** submit S iff P(y(S) > banked) ≥ p* AND
  E[hidden(S) − hidden(banked) | y(S) > banked] ≥ 0 under the posterior (the second
  condition is what the ±0.003 tracking-noise argument approximates; with calibrated
  predictive it is computable). Micro-promotions pass only when the predictive, not the
  vote-gap heuristic, says so.
- **Final slots:** portfolio pick maximizing P(max ≥ target) over posterior-predictive
  samples (HVZ construction: competitive mean, high variance, low correlation with banked).
- Signals (pu-class) may gate/tie-break (passive, retrodiction-supported) but never select
  pools (active) without a paid scale test — the measured Goodhart clause, now policy.

## 10. Improved uncertainty quantification

(i) Gibbs-η posterior (calibrated temperature); (ii) δ spike-slab adds honest member-level
dispersion where the family is blind; (iii) conformal wrapper: predictive intervals for a
new read = model interval ⊕ empirical quantile of the 8 probe residuals (finite-sample
valid, assumption-light); (iv) report both model-based and conformal boxes on every
pre-registration (they should agree when the machinery is healthy — divergence is itself
an alarm).

## 11. A 20-submission optimal schedule (and its mapping to the real remaining budget)

Design assumption: 20 reads, best-score-counts, bench/primary split available; update after
every read (SMC makes this minutes). EIG values are computed at design time by §8; the
schedule below states the *policy*; the specific pools come out of the covariance each round.

| # | Type | What changes | Tests / expected effect |
|---|---|---|---|
| 1–2 | Eigen-probe v₁, v₂ (bench) | ±1.5–2.5K coherent swaps along top uncertainty modes | Resolves dominant posterior modes; expected entropy drop ≈ ½log(1+λ₁/σ²) each — the largest available anywhere |
| 3 | Null-space probe (bench) | 3–4 rider blocks on never-excited directions | First-ever information on dead coefficients; kills or revives them |
| 4–5 | δ-cohort probes (bench) | Largest unmeasured spike-slab mass × decision relevance (e.g., no-line cohort level; residual never-probed pool slice) | Converts prior δ-mass into measured π_c; directly reprices ~2–7K candidate members |
| 6 | Adequacy probe (bench) | Surrogate-optimal far candidate, trust-capped | Separates θ-error from δ-mass at the frontier (the v32 question, asked properly) |
| 7–12 | Alternate: greedy-EIG probe / Thompson exploit (bench→primary as guards allow) | Exploit = top-K of a posterior draw, capped | Switch rule: exploit when KG value ≥ max EIG × (marginal value of information); Thompson keeps free upside while still constraining the posterior |
| 13–17 | Vetted exploit tranches (primary) | Calibrated-predictive promotions (the v34 pattern, now predictive-gated) | Each expected +0.001–0.003 while pool freshness lasts; stop when predictive gain < replacement risk |
| 18–19 | Portfolio finalists (primary) | Two HVZ-style decorrelated candidates | Maximize P(max ≥ target); backup decorrelated at the boundary |
| 20 | Reserve/filler | Best banked variant only if a slot would expire | Never spend E-negative under the two-LB rule |

**Mapping to reality (7 bench + 3 primary, ~4 days):** run rows 1–2 and 4 on the bench
(three reads), then one adequacy-or-Thompson bench read, keeping 3 bench in reserve;
primary gets two predictive-gated promotions plus the final portfolio pick on 7/8.

## 12. Ablation plan

On the simulator (§13) and the 30-read archive (retrodiction): (a) η-calibrated vs uniform
ensemble weights — metric: probe-coverage and far-candidate bias; (b) covariance vs
marginal-vote probe selection — metric: entropy trajectory and realized info/read;
(c) with/without δ layer — metric: predictive log-score on the 5 measured pools;
(d) SMC vs 48-restart DE at equal evaluation budget — metric: kept-set diversity and fit;
(e) OBS_POW ∈ {0, 2} — metric: LOO on early reads; (f) exploit scheduling: Thompson vs KG
vs current heuristic — metric: simulated E[max read] over 100 replications.

## 13. Simulation framework (the missing tool that de-risks everything)

Generator: sample θ* from the current posterior; sample δ* by cohort with the *measured*
pool densities (parity/−0.41/−0.29/≈0 anchors + spike-slab elsewhere); t* = topK(g_θ*)⊕δ*;
simulate reads as Binomial-thinned counts (the exact 70/30 mechanism, σ validated against
A42). Then run *whole policies* (current heuristic loop vs redesigned loop) for 20
synthetic reads × ≥100 truth replications; report E[final max], entropy trajectories,
coverage, and policy regret with CIs. Cost: a day of implementation on existing artifacts
(mask caches, swap builders); zero leaderboard spend. Rule: no policy change ships without
beating the incumbent on the simulator.

## 14. Risk analysis

- **Gaussian EIG approximation** at discrete counts: mild; guarded by sizing probes ≥5σ.
- **Surrogate bias** near the cutoff: bounded by exact-φ acceptance; ablate.
- **δ-model mis-binning** (cohorts too coarse): the probes measure whatever pool is
  submitted — mis-binning wastes efficiency, not validity.
- **Goodhart on any signal used actively:** policy §9 forbids it; the v43 event is the
  standing exhibit.
- **Process risk:** the redesign must not destabilize a working pipeline in the final days
  — hence the retrofit ordering in §15 (reweight first, replace later) and the simulator
  gate before any live change.
- **Governance:** unchanged by this document; bench reads carry the standing, user-owned
  multi-account exposure; nothing here increases it beyond the already-accepted pattern.

## 15. Implementation roadmap

1. **Tonight (hours):** η/τ calibration + importance reweighting of the existing 25-fit
   ensemble (fixes calibration everywhere downstream); eigen-probe designer on the fresh
   refit-30 masks; conformal wrapper on the 8 probe residuals.
2. **Day 2:** simulator + policy A/B; SMC retrofit of the fit loop (population reuse);
   δ bookkeeping formalized (five measured pools as likelihood terms).
3. **Ship:** next bench reads from the eigen-probe designer; primary promotions gated by
   the calibrated predictive; final-slot portfolio rule on 7/8.
4. **Post-competition (R2/R3):** this document + the measured exhibits (identifiability
   audit, Goodhart closure, probe ledger) as the methodology story.

## 16. Prioritized recommendations

| # | Recommendation | Expected gain | Info/read | Ease | Novelty | Replaces/augments |
|---|---|---|---|---|---|---|
| 1 | Gibbs-η reweighting + τ (calibration) | Fixes measured bias; +decision quality everywhere | — | **Hours** | Low (textbook, correctly applied) | Replaces λ + edge-model |
| 2 | Eigen-probe designer (covariance EIG) | ~1.5–2× info per bench read | **High** | **Tonight** | Medium (BatchBALD→counting queries) | Replaces axe-list probe selection |
| 3 | δ spike-slab layer | Honest member-level UQ; formalizes probes | Med | 1 day | Medium | Augments; replaces veto's role partially |
| 4 | Conformal boxes | Valid intervals from 8 residuals | — | **Hour** | Low | Augments pre-registration |
| 5 | Simulator + policy regret | De-risks all changes; quantifies policies | — | 1 day | Med | New capability |
| 6 | SMC/CE optimizer retrofit | 5–10× compute; per-read updates | Med | 1–2 days | Low | Replaces 48-restart DE |
| 7 | Thompson/KG scheduling | Optimal explore/exploit switch | Med | ½ day | Med | Replaces heuristic scheduling |
| 8 | Soft-top-K surrogate | Speed only | — | 1 day | Med | Augments optimizer |
| 9 | Amortized DAD-style design | Marginal at this scale | Low | Weeks | High | **Rejected** — overkill |
| 10 | BT/Plackett–Luce/Mallows reformulations | None — no pairwise/listwise feedback exists | — | — | — | **Rejected** — category error for this channel |

**Direct answers to the mission's standing questions.** *Can the framework be reformulated
as a stronger statistical object?* Yes: a Bayesian inverse problem with a generalized
likelihood over (θ, δ) and sequential (SMC) updating — §5–7; probabilistic-programming or
HMC machinery adds nothing because φ is discontinuous (SMC/ABC is the right family), and
differentiable-ranking makes gradients available only for proposals. *Would it need fewer
submissions?* Yes — retrospectively ~15–18 optimally designed reads reproduce the archive's
information content (the redundancy audit is the evidence); prospectively, expect
+30–60% information per bench read and strictly better-calibrated primary decisions.

---

## Annex A — Verified citations (independent web-verification pass, 2026-07-04)

All 30 verified; two strings corrected (#4 full subtitle; #25 is arXiv-only — no journal).

1. Lindley (1956) "On a Measure of the Information Provided by an Experiment", Ann. Math. Stat. 27(4).
2. Chaloner & Verdinelli (1995) "Bayesian Experimental Design: A Review", Statistical Science 10(3).
3. Foster, Ivanova, Malik, Rainforth (2021) "Deep Adaptive Design: Amortizing Sequential Bayesian Experimental Design", ICML.
4. Ivanova, Foster, Kleinegesse, Gutmann, Rainforth (2021) "Implicit Deep Adaptive Design: Policy-Based Experimental Design without Likelihoods", NeurIPS.
5. Rainforth, Foster, Ivanova, Bickford Smith (2024) "Modern Bayesian Experimental Design", Statistical Science 39(1).
6. Golovin & Krause (2011) "Adaptive Submodularity…", JAIR 42.
7. Houlsby, Huszár, Ghahramani, Lengyel (2011) "Bayesian Active Learning for Classification and Preference Learning", arXiv:1112.5745.
8. Kirsch, van Amersfoort, Gal (2019) "BatchBALD…", NeurIPS.
9. White (1982) "Maximum Likelihood Estimation of Misspecified Models", Econometrica 50(1).
10. Bissiri, Holmes, Walker (2016) "A General Framework for Updating Belief Distributions", JRSS-B 78(5).
11. Grünwald & van Ommen (2017) "Inconsistency of Bayesian Inference for Misspecified Linear Models…", Bayesian Analysis 12(4).
12. Knoblauch, Jewson, Damoulas (2022) "An Optimization-centric View on Bayes' Rule…", JMLR 23(132).
13. Toni, Welch, Strelkowa, Ipsen, Stumpf (2009) ABC-SMC, J. R. Soc. Interface 6(31).
14. Del Moral, Doucet, Jasra (2012) adaptive ABC-SMC, Statistics and Computing 22.
15. Hansen (2016) "The CMA Evolution Strategy: A Tutorial", arXiv:1604.00772.
16. Rubinstein (1999) Cross-Entropy Method, Methodol. Comput. Appl. Probab. 1(2).
17. Blondel, Teboul, Berthet, Djolonga (2020) "Fast Differentiable Sorting and Ranking", ICML.
18. Cuturi, Teboul, Vert (2019) "Differentiable Ranking and Sorting using Optimal Transport", NeurIPS.
19. Xie et al. (2020) "Differentiable Top-k with Optimal Transport", NeurIPS.
20. Petersen, Borgelt, Kuehne, Deussen (2022) "Monotonic Differentiable Sorting Networks", ICLR.
21. Plan & Vershynin (2013) "One-Bit Compressed Sensing by Linear Programming", CPAM 66(8).
22. Quadrianto, Smola, Caetano, Le (2009) "Estimating Labels from Label Proportions", JMLR 10.
23. Brahmbhatt, Saket, Raghuveer (2023) "PAC Learning Linear Thresholds from Label Proportions", NeurIPS (spotlight).
24. Javanmard, Fahrbach, Mirrokni (2024) "PriorBoost: An Adaptive Algorithm for Learning from Aggregate Responses", ICML (spotlight).
25. Hunter, Vielma, Zaman (2016, v3 2019) "Picking Winners in Daily Fantasy Sports Using Integer Programming", arXiv:1604.01455 (preprint).
26. Russo, Van Roy, Kazerouni, Osband, Wen (2018) "A Tutorial on Thompson Sampling", FnT ML 11(1).
27. Frazier, Powell, Dayanik (2008) "A Knowledge-Gradient Policy for Sequential Information Collection", SIAM J. Control Optim. 47(5).
28. Angelopoulos & Bates (2023) "Conformal Prediction: A Gentle Introduction", FnT ML 16(4).
29. Chen, Lin, King, Lyu, Chen (2014) "Combinatorial Pure Exploration of Multi-Armed Bandits", NIPS 27.
30. Aldous (2021) "A Prediction Tournament Paradox", The American Statistician 75(3).

**Addition surfaced by the verification pass:** Xie, Cao & Xu (2026) "Adaptive Combinatorial
Experimental Design: Pareto Optimality for Decision-Making and Inference", AISTATS 2026
(arXiv:2602.24231) — formalizes the regret-vs-inference-power Pareto frontier for designs
where each pull must simultaneously score and measure: the exact dual objective of a
best-score-counts leaderboard submission. Adopted as the theoretical frame for §11's
probe-vs-exploit switch rule.

_Annex B will record the simulator's policy-regret results once built._
