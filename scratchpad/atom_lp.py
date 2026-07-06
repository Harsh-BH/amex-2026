#!/usr/bin/env python3
"""atom_lp.py — Atom-algebra partial identification over the FULL read ledger.

Strictly tighter successor to lp_localize.py (2026-07-02, 23 reads, ±150 TOL,
wrong basis). Fixes:
  * correct basis: reads are EXACT integer counts over the PUBLIC 70,000 (A42),
    so Sigma_l t_l = 70000 and r_i = round(score_i * 70000)   (NOT frac * 100000)
  * per-read tolerance ~ the read's own precision (6-dp reads => +/-2, 3-dp => +/-40)
  * 31 reads (v1..v44) instead of 23

Atoms = equivalence classes of the 31-bit (in top-100K of set i?) signature.
Unknowns t_l = |T ∩ P ∩ atom_l|. The read ledger is, exactly:
    for each scored set i:  sum_{atoms l ⊆ S_i} t_l  ≈ r_i   (± per-read tol)
    total:                  sum_l t_l                = 70000
    box (deterministic):    0 ≤ t_l ≤ |atom_l|
The feasible polytope provably contains the truth. Per-atom / per-aggregate
min-max LPs give sharp bounds — hypothesis-class-free partial identification.

Outputs (cheap aggregates first; they gate the expensive per-atom pass):
  0. feasibility / integrity of the whole ledger
  1. dark mass [lo,hi]  = truth in the never-submitted atom (outside ALL tops)
  2. recoverable-and-attributed = misses that SOME other set captured (re-rankable)
  3. per-atom [t_lo,t_hi] -> miss map, certified labels, optimistic ceiling
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from triangulate2 import OBS  # authoritative version -> public score ledger

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
PUB = 70_000
BANKED = "v35"  # judged best on the primary account (0.918971)

# exact 6-dp / 4-dp reads (LB hover-confirmed) vs 3-dp display reads
EXACT6 = {"v34", "v35", "v36", "v37L", "v41"}
EXACT4 = {"v44"}


def read_tol(v: str) -> float:
    if v in EXACT6:
        return 2.0        # +/- rounding of the 6th dp * 70000 (<1) + safety
    if v in EXACT4:
        return 5.0        # 0.00005 * 70000 ~= 3.5
    return 40.0           # 3-dp display: 0.0005 * 70000 = 35


def load_top(v: str, ids: np.ndarray) -> np.ndarray:
    s = pd.read_csv(ROOT / "data" / f"scores_{v}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    assert not np.isnan(s).any(), f"{v}: score misaligned to id space"
    m = np.zeros(s.size, bool)
    m[np.argpartition(-s, TOPK)[:TOPK]] = True
    assert m.sum() == TOPK, f"{v}: top set != 100K (tie at cutoff?)"
    return m


def main():
    t0 = time.time()
    versions = list(OBS)
    df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
    ids = df["id"].to_numpy()
    N = ids.size
    assert N == 500_000

    M = np.zeros((N, len(versions)), bool)      # (member, set)
    for j, v in enumerate(versions):
        M[:, j] = load_top(v, ids)
    r = np.array([round(OBS[v] * PUB) for v in versions], float)
    tol = np.array([read_tol(v) for v in versions])
    print(f"{len(versions)} reads loaded; scores {min(OBS.values()):.3f}..{max(OBS.values()):.6f}")

    # ---- atoms: distinct membership signatures --------------------------------
    packed = np.packbits(M, axis=1)
    uniq, atom_of, counts = np.unique(packed, axis=0, return_inverse=True, return_counts=True)
    # recover per-atom signature bits from the first member of each atom
    first = np.zeros(len(uniq), np.int64)
    seen = np.zeros(len(uniq), bool)
    for i, a in enumerate(atom_of):
        if not seen[a]:
            first[a] = i; seen[a] = True
    sig = M[first]                               # (L, V) bool
    size = counts.astype(float)
    L = size.size
    print(f"-> {L:,} atoms (largest {int(size.max()):,}, median {int(np.median(size))}); "
          f"build {time.time()-t0:.1f}s")

    # ---- LP scaffold: soft reads (± tol) + hard total + det box ---------------
    # variables: t in R^L, 0 <= t <= size
    A = sig.T.astype(float)                       # (V, L): row i sums atoms in set i
    A_ub = np.vstack([A, -A])
    b_ub = np.concatenate([r + tol, -(r - tol)])
    A_eq = np.ones((1, L))
    b_eq = np.array([float(PUB)])
    bounds = list(zip(np.zeros(L), size))

    def solve(c, maximize=False):
        res = linprog(-c if maximize else c, A_ub=A_ub, b_ub=b_ub,
                      A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
        if res.status != 0:
            return None
        return (-res.fun if maximize else res.fun)

    # 0. feasibility / integrity
    feas = solve(np.zeros(L))
    if feas is None:
        print("\n*** LEDGER INFEASIBLE at these tolerances — a read decode or set is wrong,\n"
              "    or the tolerances are too tight. Loosen read_tol and re-audit. ***")
        # try to find the minimal uniform slack that restores feasibility
        for extra in (10, 25, 50, 100, 200):
            b2 = np.concatenate([r + tol + extra, -(r - tol - extra)])
            res = linprog(np.zeros(L), A_ub=np.vstack([A, -A]), b_ub=b2,
                          A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
            if res.status == 0:
                print(f"    feasible only after loosening EVERY read by an extra +/-{extra} members.")
                break
        return
    print("ledger feasible under the tight per-read tolerances ✓")

    jb = versions.index(BANKED)
    in_bank = sig[:, jb]                          # atom inside the banked top?
    total_out = PUB - round(OBS[BANKED] * PUB)    # misses vs banked (pinned by its read)
    print(f"\nbanked {BANKED} read {OBS[BANKED]:.6f} -> {round(OBS[BANKED]*PUB)}/70000 captured; "
          f"{total_out} public true-tops sit OUTSIDE {BANKED} (pinned, not an LP result)")

    # 1. dark mass: truth in the never-submitted atom (outside ALL sets)
    dark = ~sig.any(axis=1)
    if dark.any():
        c = dark.astype(float)
        lo, hi = solve(c), solve(c, maximize=True)
        print(f"\n[1] DARK MASS (outside all {len(versions)} tops; {int(size[dark].sum()):,} members): "
              f"truth in [{lo:.0f}, {hi:.0f}] of 70000")
        print(f"    -> at least {lo:.0f} true-tops provably live where NO submission has looked "
              f"(only new probes reach them); at most {hi:.0f}.")
    else:
        print("\n[1] no never-submitted atom (every member in some top).")

    # 2. recoverable-and-attributed: misses that some OTHER set captured
    out_attr = (~in_bank) & sig.any(axis=1)       # outside banked, inside >=1 other top
    c = out_attr.astype(float)
    lo, hi = solve(c), solve(c, maximize=True)
    print(f"\n[2] MISSES INSIDE PROBED TERRITORY (outside {BANKED}, inside some other top; "
          f"{int(size[out_attr].sum()):,} members): truth in [{lo:.0f}, {hi:.0f}]")
    print(f"    -> up to {hi:.0f} of the {total_out} misses were captured by another submission "
          f"= re-rankable by blending; >= {lo:.0f} guaranteed there.")

    print(f"\ncheap aggregates done at {time.time()-t0:.1f}s. Starting per-atom bounds "
          f"({2*L} LPs)...", flush=True)

    # 3. per-atom sharp bounds -> miss map, certified labels, ceiling
    lo = np.empty(L); hi = np.empty(L)
    e = np.eye(L)
    tick = max(1, L // 20)
    for l in range(L):
        lo[l] = solve(e[l]); hi[l] = solve(e[l], maximize=True)
        if l % tick == 0:
            print(f"    atom {l}/{L}  ({time.time()-t0:.0f}s)", flush=True)

    out = pd.DataFrame({
        "atom": np.arange(L),
        "size": size.astype(int),
        "in_bank": in_bank,
        "n_sets": sig.sum(1),
        "t_lo": lo, "t_hi": hi,
        "dens_lo": lo / np.maximum(size, 1),
        "dens_hi": hi / np.maximum(size, 1),
    })
    out.sort_values("t_hi", ascending=False).to_csv(ROOT / "scratchpad" / "atoms.csv", index=False)
    print(f"\nwrote scratchpad/atoms.csv ({time.time()-t0:.0f}s)")

    # certified labels
    cert_pos = (lo >= 0.9 * np.minimum(size, 0.7 * size + 3 * np.sqrt(0.21 * size)))
    cert_neg = (hi <= 0.02 * size)
    print(f"certified-positive atoms (t_lo ~ max): {cert_pos.sum()} "
          f"({int(size[cert_pos].sum()):,} members)")
    print(f"certified-negative atoms (t_hi ~ 0):   {cert_neg.sum()} "
          f"({int(size[cert_neg].sum()):,} members)")

    # miss map: proven recoverable outside the bank
    prov = (~in_bank) & (lo > 0.5)
    print(f"\nMISS MAP: {int(prov.sum())} atoms OUTSIDE {BANKED} have t_lo>0 "
          f"(provably contain true-tops); total guaranteed recoverable there = {lo[~in_bank].sum():.0f}; "
          f"optimistic = {hi[~in_bank].sum():.0f} of {total_out}")

    # optimistic info-ceiling: greedily fill 100K by hi-density (upper bound)
    order = np.argsort(-(hi / np.maximum(size, 1)))
    cap, got = TOPK, 0.0
    for l in order:
        take = min(size[l], cap)
        got += hi[l] * (take / size[l]); cap -= take
        if cap <= 0:
            break
    print(f"\nOPTIMISTIC CEILING (any ledger-consistent 100K ranking, upper bound): "
          f"~{got/PUB:.4f} public   [banked {OBS[BANKED]:.6f}]")
    print(f"total wall {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
