# Decision Log

_Append-only. One entry per durable decision: date, decision, rationale, alternatives, status.
Newest at top. Reverse a decision with a new entry referencing the old one._

---

## 2026-06-27 — Stage-6 weight calibration: `borrow_int` hedged 0.80→0.40 (sensitivity-driven)
**Decision:** Halve the lender `borrow_int` weight 0.80→0.40 in `src/score.py`. Per-term sensitivity
(`src/calibrate.py`) showed `borrow_int` = rank of lend-line **size** (`f17`) was the #1 lever — dropping it
churned 62% of the top-20% — but line size ≠ interest *earned*. Chose the **down-weight hedge** (user pick)
over redefining it utilization-aware or keeping as-is. Effect: borrow_int demoted #1→#4 lever; top-20%
rebalanced lender 64.6%→43.1% (≈ 41.5% pop share), revolver 24.6%→36.8%, transactor 10.8%→20.1%; 22.1% of
top-20% changed (Spearman 0.957); stability held (subsample 0.998, weight-perturb 0.836); no knife-edge term.
Weight table + sensitivity in [[framework-design]]; logged in [[experiment-history]] (v1.1).
**Rationale:** No label / 0-of-10 submissions → numeric calibration is premature; stage-6 = robustness +
business review only. Cutting reliance on a debatable capacity proxy de-risks the hidden 30% without re-design.
`depth`/`servicing_cost` have near-zero leverage (candidates to drop later, YAGNI).
**Verification:** `src/calibrate.py` (leverage), `src/validation.py` (stability), live v1↔v1.1 overlap. Also
built `src/compare.py` (baseline agreement) + `src/llm_judge.py` (OpenAI judge — **indifferent** vs naive spend
on contested pairs; convergent-validity cross-check, NOT ground truth). NOT submitted.
**Status:** Active. **Next: LB-informed calibration + first submission decision** (validate proxies agree, then spend #1).

## 2026-06-27 — Framework v1 design APPROVED (revenue−cost × risk, unified eq + per-segment weights)
**Decision:** Adopt `score = (Revenue − Cost) × (1 − Risk)`, all term inputs rank-normalized to [0,1],
as **one equation for all 500K** with **weights keyed by segment** (transactor/revolver/lender). Three
user-approved structural choices: **(1)** unified equation, weights shift by segment (not separate
per-segment models); **(2)** spend volume = cohort-rank of category spend `f6–f10` for the 77% with a
breakdown, falling back to `rank(f5)` for the 23% without (tagged) — never raw `f5` as primary volume;
**(3)** risk shaves the **whole** score multiplicatively. Drop `f18` (r=0.92 vs `f17`). Rewards cost =
redeemed `f21` + breakage-discounted `f4` liability. v1 weights = business priors; calibration deferred
to stage 6. Full spec → [[framework-design]].
**Rationale:** Implements the lit-converged skeleton ([[research-findings]]) with the EDA's hard findings
baked in — `f5` saturation ([[assumptions]] A1) and the CRITIC/entropy weighting trap ([[feature-notes]]).
Unified-eq keeps one defensible ranking (no gameable cross-segment merge); cohort-rank fallback invents
no data; multiplicative whole-score risk matches the prior research direction and is simplest for v1.
**Verification:** Designed via brainstorming skill; 3 decisions chosen by user. Two named v1 ceilings
logged in [[framework-design]] (risk-on-whole-score; uncalibrated weights). NOT yet implemented/scored.
**Status:** Active. **Next: implementation plan → score 500K → top-20% stability validation (no submission until it passes).**

## 2026-06-27 — Research phase CLOSED (round 3): diminishing returns; move to build
**Decision:** Stop literature scouting after 3 rounds (~70 verified works). Adopt from round 3: **(1) MIA missingness-as-signal** — encode structured-missing flags as signed terms, never fill-0 (Twala 2008); **(2) AMPI** non-compensatory aggregation as an A/B candidate vs weighted sum (Mazziotta-Pareto 2018); **(3) segment-aware transactor/revolver** profit terms, NOT raw-`f5` ranking (So-Thomas-Seow-Mues 2014; Fed FEDS 2022 — top spenders ≠ most profitable); **(4) contingent-liability `f4` discount** ~80–90% via 17–18% breakage, modulated per-member by `f21/f4` + engagement (Gault 2012, IATA, Chun 2020); **(5) 4-family label-free validation** (spectral SML, Monte-Carlo+Sobol, bootstrap rank-stability, weak-supervision proxy + Lorenz/Gini).
**Rationale:** Round 3's own verdict = diminishing returns: YES — the framework's structure is now redundantly covered; further effort better spent implementing + A/B-testing. Honors Semantic-Scholar-dead constraint (HTTP 402).
**Verification:** workflow w5q2bjobv (9 agents); resolved 6/7 flagged primaries (RI dropped); I spot-checked arXiv 1303.3257, 1605.07723 (`get_paper`). Round-3 addendum in `reports/...`; counts in [[bibliography]]; design use in [[research-findings]].
**Status:** Active. **Next action: environment setup → framework v1** (no more lit rounds unless a reviewer challenge needs a flagged numeral).

## 2026-06-27 — Lit-review gap-fill: composite-indicator + behavioral-scorecard framing added
**Decision:** Frame the deliverable explicitly as a **composite indicator** (OECD/JRC 7-step pipeline) **and behavioral profit scorecard**: sign-orient → **rank/percentile-transform** features → **objective weighting (CRITIC primary, entropy baseline)** tilted by P&L sign → **partially-compensatory aggregation** → **Monte-Carlo sensitivity validation** on top-20% stability. Optionally fuse P&L sub-rankings via **Reciprocal Rank Fusion**; consider **TOPSIS** as an alt engine. Risk/retention carries high leverage (Gupta-Lehmann-Stuart). LTR cannot be trained (no labels) — reuse only its eval framing.
**Rationale:** Closes the gaps flagged when the user asked "researched all things properly?" — the CLV/OR canon, proper LTR, MCDA weighting, segmentation/feature-eng (recovered dropped Theme E), behavioral scoring. Gives now-cited methods for weighting/normalization/validation the round-1 report lacked.
**Evidence/verification:** 2nd 11-agent workflow (w47np0wme), adversarial verify excluded 6 unverifiable items + dropped 1 mis-attributed paper. I spot-checked arXiv 2008.08662, 2402.04103 (`get_paper`) + Gupta-Lehmann-Stuart (WebSearch). 30 net-new verified works → [[bibliography]]; design use → [[research-findings]]; addendum in `reports/literature-review-r1-profitability.md`.
**Status:** Active.

## 2026-06-27 — Literature-backed framework direction (revenue−cost × risk-discount)
**Decision:** Adopt the lit-review-converged skeleton `profit_score = [Revenue − Cost] × (1 − ExpectedLossRate(risk))` (equivalently `margin × persistence − expected_loss`), with **risk discounting multiplicatively** (not additively) and **transactor-vs-revolver segmentation** (charge-only flag from `f17`/`f18` missingness). Normalize heavy-tailed dollar features (log/winsorize); validate label-free via normalized Gini + top-quintile lift + rank-stability under resampling/weight-perturbation.
**Rationale:** Converges across PCLV (arXiv:2506.22711), e-Profits (arXiv:2507.08860), EMP (EJOR 10.1016/j.ejor.2014.04.001), two-stage profit scoring (arXiv:2009.04536), RAR (EJOR S0377221712006078), transactor/revolver scorecard (DSS 2014). Gives the graded Framework writeup academic defensibility.
**Evidence/verification:** 11-agent workflow, adversarially verified; 4 agent-sourced arXiv IDs spot-checked real via `get_paper`. Full report `reports/literature-review-r1-profitability.md`; distilled in [[research-findings]].
**Caveats:** f-code→role mapping is our extrapolation (design rationale, not paper finding); MCDA/composite methods uncited in verified set; don't quote macro stats as paper findings.
**Status:** Active — feeds framework-design + weight-calibration + evaluation.

## 2026-06-26 — Treat R1 as interpretable framework design, not supervised ML
**Decision:** Build an explicit, interpretable **revenue−cost profitability equation** over `f1`–`f23`, not a black-box trained model.
**Rationale:** No target label exists; the metric rewards top-20% overlap with Amex's (likely formula-based) ground truth; the Framework sheet is graded and audited for integrity.
**Alternatives considered:** Unsupervised clustering / proxy-label ML (rejected: no label, low interpretability, gaming risk).
**Status:** Active.

## 2026-06-26 — `.claude` operating system built, redundant folders consolidated
**Decision:** Use Claude Code's real primitives (root `CLAUDE.md`, `commands/skills/agents/settings.json`) + referenced support folders; fold `context/`,`prompts/`,`docs/`,`experiments/`,`examples/` into existing folders.
**Rationale:** Avoid empty scaffolding; keep auto-loaded context lean; every file carries real content.
**Status:** Active. See `.claude/README.md` consolidation table.

## 2026-06-26 — Confirmed key data facts before modeling
**Decision:** Recorded as assumptions A1–A10 (`assumptions.md`): `f5` ≠ sum of category spends; structured missingness clusters; `f7` negatives; `id` forbidden.
**Rationale:** These are the traps that silently break a solution.
**Status:** A1,A2,A3,A7,A10 verified; others to confirm in EDA.
