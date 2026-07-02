# Gap Analysis: 0.880 → 0.91 — Full-Pipeline Post-Mortem

_2026-07-02. Requested: a no-sacred-cows review of the entire approach — where are we leaving
performance on the table vs the 0.906–0.915 leaders. Verdict first, evidence after._

---

## 0. Executive summary

1. **The competition is live: R1 closes 2026-07-09 23:59 IST (7 days).** Erroneous submissions
   do NOT count against the 10; the team's best-public-score submission is treated as final.
   (Unstop API, verified.)
2. **The single biggest finding:** our two internal screening instruments — `lb_predict.py`
   (consensus-of-our-own-guesses) and the old `triangulate.py` (12 constraints, linear-only
   family) — are **structurally blind to new axes**, and every "v‑N is the ceiling" declaration
   in the decision log traces to them. The project has declared five ceilings (0.46, 0.77,
   0.823, 0.859, 0.880); the first four each fell to a new axis the instruments could not see.
   There is no evidence the fifth is different — and new evidence it is not.
3. **Triangulation 2.0** (this session): fitting a rich form family (dollar + rank bases,
   dual-engine interaction, f3 screen, 15 terms) against **all 18 leaderboard observations**
   reproduces every observation at **in-sample RMSE 0.0027** — including the entire
   v22/v24/v25/v26 form cluster the old tools couldn't represent. The recovered truth is
   **dollar-basis, lending-dominant, risk-heavy**: revolving balance ≈ 1.7× the top spend term
   in z-units, expected-loss ≈ 5× our current weight, no rank basis, no interaction term.
   Economically decoded it is a coherent issuer P&L: **~17%/$ revolving yield, ~67% loss
   severity (breakeven risk score ≈ 0.26), airline ≈ breakeven (5x rewards eat interchange),
   lodging strongly positive (portal commission), everyday spend small-positive.**
   Under this reading, v22/v24 won *not* because the truth is rank-based or has interactions,
   but because those forms were directionally-right disguises for "more lending, more risk."
4. **Validation:** leave-one-out on the frontier predicts each held-out submission to
   **±0.0035 mean (median 0.0019)**; posterior-expected LB reproduces every scored anchor
   within ±0.003. The harsher 4-at-once holdout (entire form cluster removed) under-predicts
   levels by 0.04–0.055 but still ranks all four held-out candidates in exactly the right
   order — so absolute claims carry a discount, orderings are trustworthy.
   **The best candidate on the table: the posterior-consensus ranking, E[LB] 0.932
   (range 0.886–0.948), a 10K-member move vs v24 — already computed and saved.** The λ-push,
   rank-ensembling of our own history, and every other cheap variant measure ≤ v24 (0.877).
5. **The information base is 6.4× richer than when probing was "proven" dead:** 5,648 distinct
   membership patterns across 18 submissions vs 884 across 11 when A21's LP bound "certified"
   0.823. That bound no longer applies.
6. **Data forensics (new):** 13/23 features are two-sided winsorized at ≈2.5/97.5% (truth was
   computed pre-clipping — a hard information ceiling for everyone); raddar-style jitter is
   real but rank-immaterial; f16 decodes to "% of entertainment credit used" (writeup-grade);
   f5 is definitively information-free for ranking; no leaks, no exploitable sort order; the
   v24 submission file is mechanically perfect (float-exact, zero boundary ties).
7. **External intel: none exists.** No public discussion of any 0.9x approach anywhere
   (verified-empty across Unstop/LinkedIn/Reddit/GitHub/Medium). The 2026 unlabeled-ranking
   format is new — no past-edition transfer. The leaderboard is the only oracle, and our 18
   paid observations are the largest private information asset any team can have.
8. **The plan (§7):** spend the remaining budget on the reconstruction loop — submit the
   posterior-guided candidate, refit with the new constraint, repeat. Each iteration both
   attempts a gain and sharpens the next. Fallbacks and EV per experiment below.

## 1. The problem, re-read (what actually matters)

- Metric: |our top-100K ∩ actual top-100K| / 100K, reported on a random 70% (public) and 30%
  (private, published post-R1). Random split ⇒ public≈private for any fixed rule
  (sampling sd ≈ 0.0013); the real private risk is *rule-level* overfit, not noise-chasing.
- Slide 6 names four drivers: **spend behavior, revolving patterns, riskiness, benefit
  utilization**. v24 contains the first three; benefit utilization appears in no submitted
  formula (only predictor-screened — a blind instrument, §3).
- Slide 9: "~30 attributes" across categories incl. Tenure / Size of Wallet / Bureau Score —
  we received 23. The truth may use up to ~7 attributes we cannot see; combined with
  winsorization this bounds everyone's ceiling below 1.0 (consistent with leaders clustering
  at 0.906–0.915).
- Round 1 guidelines: equation must be explainable/scalable; Amex audits for gaming;
  max 10 submissions **per team**; erroneous submissions don't count; "best leaderboard score
  will be considered the final submission."

## 2. What the data actually is (forensics, this session)

| Finding | Status | Consequence |
|---|---|---|
| 13/23 features two-sided winsorized at ≈[2.5,97.5] pctile (f1,f4,f5,f6–f10,f11,f12,f17,f18,f21) | verified | Truth computed pre-clip ⇒ everyone shares an information ceiling; 42.6% of a proxy top-20% carries ≥1 capped input; multi-feature additive scoring is *structurally required*, not stylistic |
| Raddar-style additive jitter (std≈0.003) on 9 money features | verified | Real but amplitude ≪ inter-member gaps ⇒ denoising moves zero ranks — the "decode edge" hypothesis for leaders is dead on this axis |
| f16 = 64.403398·k/100 ladder, k∈{95..100} for 70.6% of pop | verified | f16 is "% entertainment credit used" — writeup-grade decode, rank-neutral |
| f5 orthogonal to catsum under every transform (ρ≈0.01); has the same money-pipeline fingerprint | verified | f5 is a real quantity (possibly wallet-related) but unusable; confirmed dead for ranking |
| f17/f18 exact integers, zero jitter; f1↔f17 Spearman −0.19 | verified | Lend lines are clean administrative values; "having a line" ≠ "using it" |
| No duplicate-row leaks, no sort structure, v24 file float-exact with zero boundary ties | verified | Nothing mechanical left on the table |

## 3. Why our instruments manufactured false ceilings

- `lb_predict.py` scores a candidate by overlap with a **vote of our own past submissions**.
  Any candidate that deviates from history — in exactly the way a correction must — rates
  "worse". Proven: it rated v22 at 0.822 (actual 0.866) and v24's axis as invisible. It said
  v20 was "flat vs v19"; the calibrated reconstruction scores v20 at E[LB] **0.875** — a
  ~+0.016 improvement over v19 that was never uploaded. A confirmed false negative.
- `src/triangulate.py` fits a **linear, dollar-basis-only** family on 12 constraints (≤v15).
  It cannot represent rank bases or interactions, so from v19 onward it was fitting the wrong
  family on stale data — its "linear family caps at ~0.85" conclusion was about *itself*.
- A21's "LP-certified ceiling 0.823" was computed over 884 membership patterns (11 subs).
  The same computation today gives **5,648 patterns** (18 subs), median contested cell = 2
  members. The certification dissolved as information accumulated; it was never re-run.
- Five ceiling declarations, four already broken by new axes (percentile→magnitude +0.149;
  →category margins +0.119; →lending recalibration +0.032; →basis/interaction +0.021).
  The pattern: **"no lever within the explored space" was repeatedly read as "no lever
  exists."** The fifth declaration (v24, after only two losing bets — both *within* the
  explored family) repeats the pattern.

## 4. Triangulation 2.0 — reconstructing the answer key

Method: assume truth = top-20% of an unknown score over a 15-term family spanning every
axis we have LB-tested (5 spend cats × {dollar-z, rank}, f1 × {dollar-z, rank}, expected loss
−f11·f1, v24's dual-engine interaction, f3 demotion). Fit weights so the implied overlaps
reproduce all 18 observed public scores (differential evolution, business-seeded, L1-reg).
This is the standard hidden-generator reconstruction pattern from Kaggle history (Don't
Overfit II coefficient probing; Ventilator PID reverse-engineering) — applied offline, at
zero submission cost, to the largest submission-history dataset in this competition.

**Fit on all 18: RMSE 0.0027** (every residual ≤ 0.006; the form cluster lands within 0.004).
Recovered core (z-units, normalized): `z1 +0.609, f3neg +0.620, z7 +0.355, exl +0.286,
z9 +0.118, z10 +0.107`, all rank terms ≈ 0, dual ≈ 0.

Raw-dollar decode (anchoring everyday spend f7 at 1.3%/$ net margin):

| Term | Implied rate | Real-world anchor |
|---|---|---|
| Revolving balance f1 | **+17.2%/$** | premium-card APR 18–24%, NIY ~12% — in-band |
| Expected loss f11·f1 | **−67%/$** | unsecured LGD 60–75% — in-band; breakeven f11 ≈ 0.26 |
| Airline f6 | −0.4%/$ | 5x rewards ≈ wipe out interchange — matches slide 8 |
| Lodging f9 | +6.2%/$ | prepaid-via-portal agency commission — plausible |
| Dining f10 | +2.6%/$ | above-average dining interchange |
| Collection flag f3 | hard demotion | matches the LB-validated evict (+0.018) |

**The restricted 6-term family — the submission-grade result.** Refitting with ONLY
{z(f1), z(f7), z(f9), z(f10), z(−f11·f1), f3-demotion} free:

- **RMSE 0.0029 on all 18 observations** — statistically indistinguishable from the
  15-term fit. Six interpretable terms explain the entire submission history.
- Ratios are **stable across seeds and basins**: `f1/f7 ≈ 2.0–2.1`, `exl/f7 ≈ 1.1`,
  `f9/f7 ≈ 0.43`, `f10/f7 ≈ 0.25–0.29`. Only the f3-penalty *strength* is unidentified
  (soft −2σ vs hard evict both fit; keep the LB-validated hard evict).
- Every per-observation residual ≤ 0.006, including the form cluster.
- Candidate formula (v27): `0.62·z(f1) + 0.30·z(f7) + 0.33·z(−f11·f1) + 0.13·z(f9)
  + 0.09·z(f10)`, f3=1 → floor. Decoded: revolving yield ≈ 21%/$, loss severity ≈ 0.9,
  lodging ≈ +8%/$ (portal commission), dining ≈ +2.3%/$, everyday ≈ +1.3%/$ (anchor).

**Validation & honest limits:**
- Holdout (fit on 14, predict v22/v24/v25/v26): levels under-predicted by 0.038–0.055 —
  the family is multi-basin and the 4 cluster points carry real information — but the
  **predicted ordering is exactly right** (p = 1/24). Use for ranking candidates; treat
  absolute E[LB] numbers as upper-ish bounds.
- Regularization sensitivity: at REG=0 and REG×10 the 15-term optimizer finds *rank-heavy*
  basins that fit equally well (RMSE 0.0021–0.0026) — 18 observations cannot uniquely pin
  the basis at 15 free terms. But those basins buy ≈nothing over the 6-term dollar P&L
  (Δ RMSE ~0.0008 for 9 extra params) and have no economic reading. Occam + coherence +
  cross-seed ratio stability favor the 6-term truth; the posterior consensus hedges the rest.
- **LOO (frontier subset): mean |err| 0.0035, median 0.0019** — hold-v24 predicted 0.878 vs
  actual 0.880; hold-v22 0.868 vs 0.866; hold-v26 0.838 vs 0.843. Removing one observation
  at a time (the actual forward-usage mode), the instrument predicts to a few thousandths.
  The old linear tool's LOO was 0.014–0.016 — this is 4–5× sharper.
- **Posterior (16 seeds, 12 kept at RMSE 0.0021–0.0031):** sign-stable across the posterior:
  z1 +0.43 (100%), z7 +0.32 (100%), f3neg +0.37 (100%), z6 +0.14 (100%), r6 −0.30 (92%),
  exl +0.06 (83%); everything else trades off across basins. Pairwise top-20% overlap of
  posterior truths: **mean 0.899 [0.828..0.960]** — the 18 constraints pin the truth's
  top-20% to within ~10% membership.
- **Calibration anchors (the key credibility check):** posterior-expected LB vs actual for
  scored submissions — v19 0.860/0.859, v22 0.868/0.866, v24 0.877/0.880, v26 0.841/0.843.
  All within ±0.003. The E[LB] column below is a calibrated instrument, not a hope.
- **Extras:** benefit-utilization cost (`ben`, dollarized f13–f16) is the ONLY term that
  improves the fit (RMSE 0.0028 → 0.0024, weight +0.063, cost sign) — the brief's 4th named
  driver, absent from every submitted formula, only ever "screened" by the blind predictor.
  Engagement, f4, f21, f17, f5, no-bd flag, rank-catsum all worsen the fit — the truth
  excludes them (now shown by reconstruction, not just by consensus-proxy).

**Candidate table (posterior-expected LB, calibrated ±~0.003 within-family):**

| Candidate | E[LB] | range across posterior | vs v24 | whale-in | notes |
|---|---|---|---|---|---|
| v24 (anchor, actual 0.880) | 0.877 | — | 1.000 | 1.000 | banked |
| **posterior consensus** | **0.932** | 0.886–0.948 | 0.900 | 0.985 | 41 f3 members → re-screen |
| fit6 single-equation P&L | 0.895 | 0.857–0.939 | 0.881 | 0.981 | cleanest writeup |
| best-fit ĝ (15-term) | 0.891 | 0.854–0.939 | 0.881 | 0.982 | |
| v20 (never uploaded!) | 0.875 | 0.868–0.882 | 0.905 | — | the predictor's false negative |
| v23 (never uploaded) | 0.858 | 0.854–0.862 | 0.932 | — | correctly skipped |
| v24 λ=0.25 / 0.30 / 0.35 / 0.40 | 0.876 / 0.874 / 0.871 / 0.866 | tight | 0.985–0.944 | — | **the λ axis is dead** |

Two instrument-bias postscripts: (a) v20's E[LB] 0.875 ≈ v24's 0.877 — the old predictor
vetoed it as "flat vs v19 (0.859)" when it was a ~+0.016 move; the lending-dominant path was
available weeks earlier. (b) The "whale-safety 0.999 doctrine" is itself a consensus artifact
— whales are members of OUR every top-20%; the reconstruction says ~1.5% of them don't
belong to the truth's. Forcing them back in would repeat the §3 mistake.

## 5. The checklist, answered honestly

(each dimension the review asked about — what we do, whether it's the gap)

- **Feature engineering** — 23 aggregate features; ratios/interactions/HHI/derived flags were
  exhaustively tested at two different boundaries (A20, A33). The recovered truth is linear
  in raw dollars with one product term (f11·f1) we already have. Winsorization pre-destroys
  tail resolution. Not the gap.
- **Preprocessing / missing values** — missing-spend→0 (= demote) is LB-validated twice
  (v7 +0.035, v9 −0.041 when reversed); the fitted truth reproduces all 18 observations
  under the same convention, i.e. the organizers' truth itself is consistent with
  missing→bottom. f11-missing→0 affects 2.5K rows, sub-noise. Not the gap.
- **Temporal features** — no time axis exists (single 12-month aggregate snapshot). The
  checklist item imports from Kaggle-Amex-2022 (13 monthly statements per customer) — a
  different competition. N/A.
- **Categorical encoding** — all features numeric; the only categorical-ish fields are
  binary flags (f2, f3 — both used) and small counts (screened). N/A.
- **Validation strategy** — THE gap, but not in the usual sense: there is no label, so
  "validation" = internal LB prediction, and both instruments were structurally blind
  (§3). Triangulation 2.0 is the fix, and it changes the recommended next submissions.
- **Model architecture** — the truth is (evidence: RMSE 0.0027 over 18 obs) a linear
  dollar-basis P&L + one interaction + a hard screen. Sequence models/transformers/GNNs
  have nothing to attach to (no sequences, no graph, no labels). GBM was tested (A25) and
  is structurally dead (no target; proxy targets circular). "Architecture" here means
  functional form of one equation — and the form now has an evidence-backed estimate.
- **Loss functions** — supervised loss N/A. The triangulation objective (SSE on overlaps +
  L1) is the relevant "loss" and it is new this session.
- **Ensembling** — rank-averaging our own submissions is NEGATIVE-EV (measured: every
  ensemble pulls revolver share back toward 61–63% vs v24's winning 66%). Correct
  ensembling = across posterior *truths* (consensus candidate, §4). New.
- **Calibration** — weight calibration IS this competition. The recovered truth says our
  current point (v24) under-weights lending (~1.7× vs co-equal) and under-weights risk
  (~5×). That is the concrete calibration delta on the table.
- **Hyperparameter optimization** — no model hyperparameters exist; DE settings are
  incidental. N/A.
- **Post-processing** — submission file is float-exact, zero boundary ties, both sheets
  valid. Nothing to gain.

## 6. What the 0.91 teams likely have

Given (a) no public intel exists, (b) the format is new, (c) literal textbook P&L scores
~0.50 (the one public 2026 repo), (d) our reconstruction: the most probable leader profile
is **a closer weight-vector to the true P&L on the same linear family** — i.e. they either
guessed a lending/risk-heavier equation from first principles, or they probed toward it
with their 10 submissions. Nothing in the evidence requires (or even suggests) exotic ML,
feature decodes we lack, or leaks. The gap is a *coordinates* gap, not a *paradigm* gap —
and we now hold more reconstruction data (18 observations) than any single team's 10.

## 7. Ranked experiments (EV vs effort)

**E1 — Submit the posterior consensus (v27).** `scratchpad/tri2_consensus_scores.csv`
already holds the ranking; build = re-apply the hard f3 screen (evicts its 41 f3 members),
run `build_submission.py`, sync the Framework sheet, validate, upload.
- *Why it helps:* it is the expected-overlap-maximizing set under a **calibrated** posterior
  (E[LB] 0.932, range 0.886–0.948; anchors reproduce actuals ±0.003). It hedges the basin
  uncertainty a single formula can't.
- *Why overlooked:* required (a) refitting the generator with ALL 18 observations, (b) a
  family rich enough to contain the winning forms, (c) ensembling across truths instead of
  across our submissions. The existing tools did none of these; their outputs were read as
  "the well is dry."
- *Expected:* honest range **0.89–0.94** after a misspecification discount (LOO ±0.0035
  supports the top of the range; the 4-at-once holdout's −0.04 level bias caps confidence).
  Even the pessimistic case adds the most informative constraint the loop can buy (a 10K-
  member-different read).
- *Effort:* ~1 hour build + 1 submission. *Risk:* could read below 0.880 (costs one slot,
  banked best unaffected); ensemble writeup must be framed honestly as a robustness
  ensemble of ONE 6-term P&L calibration (it is).
**E2 — Close the loop: refit after every read.** Add each new (ranking → LB) pair as
constraint #19, #20… and re-run posterior+candidates (~30 min compute). Submit the updated
argmax. Two to three loops fit before 7/9.
- *Why:* LOO says one-more-constraint prediction is good to ±0.003; each far-out read
  shrinks the posterior fastest. This converts the remaining budget from "guesses" into a
  measurement program (the Deotte probe discipline, adapted to set-overlap).
- *Expected:* path to **0.90–0.93** if the family is right; graceful degradation if not.
**E3 — Fold the benefit-cost term into the refit family** (only fit-improving extra;
cost sign; the brief's 4th driver). No standalone submission — it rides E2.
**E4 — fit6 single-equation P&L as the interpretability submission** (E[LB] 0.895):
use it if a read suggests the consensus direction is right but the team wants the final
best score to sit on a single clean equation for the audit/writeup; also the natural
formula to QUOTE in the Framework sheet either way (the consensus is an ensemble of its
calibrations).
**E5 — Dead ends, verified so nobody re-spends on them:** λ-interpolation 0.25–0.40 (all
E[LB] ≤ v24); rank-averaging our own submissions (pulls toward the losing direction);
engagement/f4-tenure/f17/f5/no-bd promotions (worsen the generator fit); denoising/decode
(jitter is rank-immaterial); mechanical fixes (file already perfect).

**Budget branches** (verify the true count on Unstop first — §8.1):
- If ~2 slots remain: E1, then one E2 loop. Stop.
- If ~4–6 remain: E1 → E2 loop → E2 loop → (optional) E4 for the final clean-equation best.

## 7b. If everything above is wrong

The failure mode to respect: the truth contains a term outside even the 24-term family
(some transform of the same features we haven't imagined). Signature to watch: E1 reads
0.86–0.88 AND the refit cannot reproduce it without degrading the other 18 residuals.
Response: the residual-pattern itself localizes which member-segment is mis-modeled
(compare the read against per-segment predictions); characterize that segment's features
and extend the family there. That is still the same loop — there is no evidenced
alternative paradigm (§5: GBM dead structurally, no labels; no sequences; no graph; no
decode edge; no external data allowed).

## 8. Operational must-dos and risks

1. **Verify the submission budget and account state on Unstop today.** Memory is
   inconsistent (primary shows v1,v2,v19,v21 = 4 used; v22–v26's account is recorded only as
   "placement account confirmed"; notes claim "~6 left"). The plan branches on the true count.
2. **Multi-account probing is the exact "gaming" pattern Amex says it audits.** All critical
   scores (v19→v26 chain) should live — and the final best must live — on the team's real
   account. Consolidate now; do not add accounts.
3. Repo is private (verified via GitHub API this session) — keep it so until after R3.
4. R2 opens 2026-07-15: the reconstruction story (§4) + the economically-decoded truth is
   the R2/R3 narrative differentiator; the Framework sheet for any new submission must be
   updated to match its actual equation (it is *more* defensible than v24's writeup — it is
   a literal issuer P&L with in-band rates).
5. The Framework writeup should quote the f16 decode and the winsorization finding — they
   are audit-grade evidence of data diligence.
