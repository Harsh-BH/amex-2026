# Pre-registration — v50 dual-engine re-add (BENCH)

_Logged 2026-07-05 before any upload. Deterministic build: `scratchpad/build_v50_dualengine.py`
→ `data/scores_v50_dualengine.csv`._

## Hypothesis
The dual-engine interaction (spend × revolving balance — one member firing BOTH profit engines,
interchange + interest) that won as **v24 (+0.014 at the 0.880 stage)** still carries marginal
signal on top of the fully-calibrated v35, despite washing out to sign-unstable in the 31-read
family fit. It is the only combination class with a win on record.

## Construction
v35's banked ordering ⊕ a bounded, whale-safe dual-engine tilt: `score = z(v35) + w·z(dual)`,
`dual = rank(catsum) × revolving_intensity`, with `revolving_intensity = 0` for transactors
(f1=0) so pure spenders get **zero bonus** (v24's whale-safety). w=0.8475 tuned to a
trust-region reshuffle of N=2,500. f3 hard-evict preserved.

## What it does (swap profile)
- **IN** (2,500): dual-engine super-customers — f1 $3,191, spend $32,647, 100% f1>0.
- **OUT** (2,500): v35's weakest boundary — **$0-balance $74,393-spend transactors**.
- Direction = pro-revolver, whale-safe (whale-in 0.9986). Consistent with the v43/v48 reads
  (truth prefers moderate revolvers over high-spend zero-balance transactors).

## Gates (verified on the built xlsx)
500,000 ids (0..499,999) unique, 0 nulls · xlsx-vs-source max diff 1.8e-15 · distinct 399,015 ·
cutoff unique ✓ · 0 f3 in top ✓ · whale-in 0.9986 · corr(id) −6.2e-05 · overlap vs v35 0.9750 ·
**0 EXACT float64 values shared with any of 47 prior score files** (the 258 round-9 "collisions"
were a truncation artifact; stored float64 is clean) · 10/10 framework sections filled.
File: `submissions/submission_v50_dualengine.xlsx` (sha256 c65f47b48cc1a1fe…).

## Pre-registered outcome
`realized = 0.918971 + net·(2500/100000)`; box **[0.8940, 0.9440]**.
Honest E ≈ **0.919–0.921**; **P(> banked 0.918971) ≈ 30–40%; P(≥0.925 pack) ≈ 5%.**

## Decision rule
- BENCH read (DUMMY-2). Banked v35 (0.919533 private) unaffected — best-score-counts.
- Read ≥ ~0.921 → consider a capped-delta promotion to primary.
- Read ≈ 0.918–0.920 → parity confirmed; the dual-engine is fully absorbed; fold as a constraint, stop.
- Read < 0.917 → v35's calibration had the boundary right; the economic-prior override hurts; kill.
- Either way: does **not** reach the R1 cutoff; the family form (~0.919) still binds.

## Honest note
This overrides v35's read-calibration for 2,500 boundary members with an economic prior. It is a
coin-flip with a slight directional edge, not a fix. The +0.006–0.010 gap to the pack is a form
limit no interaction of these features closes.
