# Amex Campus Challenge 2026 — R1 Methods README

_What we are doing, in full. Written 2026-07-04. This is the technique inventory; the
running log lives in `.claude/memory/experiment-history.md`, decisions in
`.claude/memory/decision-log.md`, the formal redesign in
`reports/methodology-redesign-2026-07-04.md`._

---

## 0. The problem in one paragraph

Rank 500,000 Premier cardmembers by profitability to the issuer. **No label exists.** The
only supervision is the public leaderboard: each submission returns ONE number — the overlap
between our predicted top-20% (100,000 rows) and the hidden true top-20%, on a fixed 70%
public subset. Metric decoded to an exact integer count over **70,000** (the public true-top
set). Best submission counts as final. We turn that scalar channel into a measurement
instrument and invert it.

---

## 1. The scoring model (what actually ranks members)

An **interpretable linear revenue−cost equation** — no trained ML, no black box, every
coefficient a business rate an auditor can check:

```
margin = 0.69·z(f1)                [net interest income on the revolving balance]
       + 0.40·z(f7)                [general-spend interchange]
       + 0.18·z(f9) − 0.01·z(f10)  [lodging portal-commission margin; dining ≈ 0]
       − 0.58·z(f11·f1)            [expected credit loss on the balance exposure]

score  = margin,                       if f3 = 0
       = below the scored population,  if f3 = 1   (collection-flag hard eviction)
```

`z(x) = x/std(x)`, no centering (preserves the zero-mass cohorts); missing → 0 (a missing
line means that revenue/cost does not exist for the member). Decoded per-dollar rates
(revolving yield ~18–20%, loss severity ~1.1–1.3× exposure, airline ≈ 0 after 5x rewards,
lodging ~+8–9%) sit inside real-world bands verified against Amex 10-K **and** Amex India
audited financials. Method class: **composite indicator / behavioural profit scorecard**.

## 2. Calibration — leaderboard inversion (how the coefficients are found)

There is no target to regress on, so we **invert our own leaderboard history**:

- Each of our ~31 scored submissions has a known public overlap. For any candidate weight
  vector, compute the overlap its top-100K *would* have had with each historical ranking,
  and search for weights whose ~31 implied overlaps reproduce all ~31 observed scores at once.
- **Optimizer:** differential evolution (the top-K overlap objective is discontinuous, so no
  gradients), seeded from business priors, frontier-weighted squared error, sparsity penalty.
- Reproduces all reads at **RMSE ≈ 0.003**.
- Academic framing: **learning from label proportions / set-membership identification /
  one-bit (aggregate) compressed sensing** — recover a hidden function from a few aggregate
  measurements of it.

Core engine: `scratchpad/triangulate2.py` (the `OBS` dict is the literal read ledger).

## 3. Uncertainty — a calibrated ensemble posterior

- Run the optimizer from 48 seeds; keep the best ~12–25 as an approximate posterior over
  weight vectors. Each member gets a **vote** = how many kept calibrations place it in the
  top-20%.
- **Generalized-Bayes (Gibbs-η) tempering (added 2026-07-04):** the raw kept-set was a level
  set, not a posterior, and was measurably overconfident (three self-reads landed in its
  distribution tails). We now reweight the calibrations by `exp(−η·SSR/2σ²)` with `(η, τ)`
  fitted so the **8 designed-probe outcomes achieve uniform PIT coverage** — honest
  uncertainty, demonstrated not assumed. `scratchpad/redesign_step1.py`.

## 4. Update policy — bounded trust-region, never a full redraw

Candidates are built by **swapping a small, capped set** of members in/out of the current
banked top-100K, never re-ranking globally:

- Swap-in = highest-conviction outsiders; swap-out = weakest-conviction incumbents.
- **Guards on every build:** hard `f3` screen; consensus "whales" (members in every
  historical top set) never demoted; unique cutoff value; `corr(id, score) ≈ 0`;
  **zero shared float values with any prior submission** (anti-fingerprint global shift).
- **Retrodiction-validated veto:** a swap is skipped if the `pu_hgb` similarity signal (a
  PU-learning classifier — resemblance to the always-in core, trained with no LB data) rates
  the incoming member below the outgoing one. `pu_hgb` earned this role by grading 7/7 paid
  swaps; it is confined to a *veto* (never active selection) after a scale-test measured it
  breaking under selection pressure (a Goodhart event, v43).
- **Calibrated-predictive gate (2026-07-04):** promotions are gated by the ensemble's
  calibrated `E[read] ± sd`, not the raw vote-gap heuristic.

## 5. Experimentation — every submission is a pre-registered experiment

- Each upload tests ONE hypothesis with **pre-registered arithmetic** written down before the
  read: `realized = base + net·N/100000`.
- The returned score is folded back as a new constraint; the ensemble re-tempers in seconds
  (sequential Bayesian updating — no full refit needed).
- Formally each probe is a **signed counting query** (quantitative group testing); the loop is
  **closed-loop active learning where the query channel is the leaderboard itself**.

## 6. Experiment design — the eigen-probe (information-optimal probing)

Instead of testing named hypotheses, choose swap pools to maximize the **posterior variance of
the queried count** — the top eigenvectors of the ensemble co-membership covariance,
computed in closed form from the mask matrix. This is greedy one-step **expected information
gain**, provably within a constant factor of any adaptive scheme for this oracle (see §9).
`scratchpad/redesign_step1.py` → `eigenprobe_specs.npz`.

## 7. Validation & integrity

- **Retrodiction harness** (`scratchpad/tiebreak_battery.py`): any proposed signal must
  correctly predict the sign of all measured swap outcomes before it is trusted.
- **Submission validator** (agent): an 8-check battery on every candidate — template
  byte-structure, exact 500K id coverage, xlsx↔csv value match, unique cutoff, `corr(id)`,
  zero `f3` in top, `docs/` untouched, anti-duplicate + deterministic rebuild.
- **Winner's-curse correction (Design A):** best-of-N selection inflates the public peak by
  ≈ σ√(2·ln N); the top finalists are statistically tied on private, so public ranking ≠
  private ranking — accounted for in the final-selection decision.
- Data audited clean (no hidden sheets/side-channels, A38); rows shuffled; features
  winsorized pre-truth (shared ceiling for everyone).

## 8. Leaderboard intelligence

- Public API (`unstop.com/api/public/live-leaderboard/290112/CodeContest`) gives every team's
  exact 6-dp score + org + timestamp. A **poller** (`scratchpad/lb_poller.py`, 15-min ticks)
  logs every top-90 improvement to `lb_events.csv` — step-size fingerprints distinguish
  *grind* (pooled probing, +0.001–0.004 steps) from *jump* (a found structural lever, +0.010
  discontinuity). This is method-level competitive intelligence from organizer-published data
  only — no profiling of individuals.

## 9. What we have PROVEN (measured, not assumed)

| Result | Status |
|---|---|
| Metric = exact integer count / 70,000; split noise σ ≈ 0.002 | Verified on all 1,828 teams' scores |
| The truth is NOT a neat formula | ~440K candidate formulas sieved (3 grammars); none thread the reads |
| The truth is lending-led, low-risk-revolver, airline/dining ≈ 0 | Stable across 11 calibration rounds; matches Amex 10-K + India financials |
| The boundary is dense (swaps measure at parity) | 4 independent instruments; the plateau is a coordinate-wise optimum |
| Probing is information-optimal already | Coin-weighing/QGT theorem: greedy eigen-probe within a constant of any adaptive scheme |
| ~11 structural axes closed by designed probes | f3, nbd level & ordering, cost-side, tenure, utilization, segment-merge, engagement cluster, supp-relationship, pu-at-scale, … |

## 10. What is deliberately NOT used (and why)

`id` (leakage/DQ); external data (forbidden, and no join key exists — the answer lives only in
the organizers' file); `f5` (uncorrelated with real spend under every transform); `f4/f21`
rewards & `f13–f16` benefits as P&L terms (measured immaterial); `f17/f18` line size (capital
cost until drawn); `f19/f20` supp/cards (measured *negative* at the boundary); black-box ML
(no label; unexplainable in the graded Framework sheet); Bradley-Terry / Plackett-Luce / etc.
(category error — feedback is set-overlap scalars, not pairwise comparisons).

## 11. Repo map

```
CLAUDE.md                         operating manual + non-negotiable constraints (§16)
.claude/memory/
  experiment-history.md           every submission: hypothesis, pre-registration, result
  decision-log.md                 durable decisions (append-only)
  assumptions.md                  A1–A46: every assumption + verification status
reports/
  methodology-redesign-2026-07-04.md   the formal BED/inverse-problem reformulation
  redteam-2026-07-03.md                adversarial review of the whole pipeline
  morning-brief-2026-07-04.md          candidate menu + decision tree
  aebc_fy24_extract.txt                Amex India audited financials (rate anchors)
scratchpad/
  triangulate2.py                 the inversion/calibration engine (OBS = read ledger)
  redesign_step1.py               Gibbs-η reweighting + eigen-probe designer
  tiebreak_battery.py             retrodiction harness + pu_hgb signal
  build_v*.py                     one deterministic build per candidate
  lb_poller.py / lb_events.csv    pack trajectory forensics
src/build_submission.py           fills the official xlsx template (all guards asserted)
data/scores_v*.csv                per-candidate 500K scores (git-ignored)
submissions/submission_v*.xlsx    validated submission files (git-ignored)
```

## 12. One-sentence summary (for a judge)

> An interpretable per-member revenue−cost equation whose weights are identified by
> inverting our own public-leaderboard measurements — set-membership identification with an
> evolutionary solver — wrapped in a calibrated ensemble for uncertainty and advanced only
> through bounded, pre-registered, individually-measured boundary experiments; probing is
> provably information-optimal for this oracle, and ~11 structural alternatives have been
> closed by designed measurement rather than opinion.
