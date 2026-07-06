#!/usr/bin/env python3
"""probe_triage.py — LP triage of the final categorical-probe hypotheses (0 reads).

The atom-LP (A47) can't localize misses open-endedly, but it CAN sharply answer
targeted questions: "how much truth-mass can pool Q hold, given all 31 reads?"
Use it to veto/rank the three never-read hypotheses before spending the probe:

  H-f2   truth demotes cancellation-callers (f2>=1)      -> evict them from the top
  H-ben  truth books benefit cost / engagement (f13-f16) -> demote or promote by it
  H-f5   truth has a standalone f5 'Total Spend' term    -> promote top-f5 outsiders

For each pool: [t_lo, t_hi] = LP min/max of |truth ∩ P ∩ Q| under the 31 exact
read-equations (± per-read tol), Σt = 70,000, 0 <= t <= |cell|.
For H-f2 the pre-registration box is the JOINT LP bound of (t_in − t_out).
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from triangulate2 import OBS

ROOT = Path(__file__).resolve().parent.parent
TOPK, PUB = 100_000, 70_000
BASE = "v37L"   # probe base set (best-ever measured, exact 6-dp read 0.919143)
EXACT6 = {"v34", "v35", "v36", "v37L", "v41"}
EXACT4 = {"v44"}
TOL = {v: (2.0 if v in EXACT6 else 5.0 if v in EXACT4 else 40.0) for v in OBS}


def top_mask(v: str, ids: np.ndarray) -> np.ndarray:
    s = pd.read_csv(ROOT / "data" / f"scores_{v}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    m = np.zeros(s.size, bool)
    m[np.argpartition(-s, TOPK)[:TOPK]] = True
    return m


t0 = time.time()
df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
ids = df["id"].to_numpy()
N = len(df)
versions = list(OBS)
M = np.zeros((N, len(versions)), bool)
for j, v in enumerate(versions):
    M[:, j] = top_mask(v, ids)
r = np.array([round(OBS[v] * PUB) for v in versions], float)
tol = np.array([TOL[v] for v in versions])
pat = np.zeros(N, np.int64)
for j in range(len(versions)):
    pat |= M[:, j].astype(np.int64) << j
base = M[:, versions.index(BASE)]
sbase = pd.read_csv(ROOT / "data" / f"scores_{BASE}.csv").set_index("id")["score"].reindex(ids).to_numpy()
print(f"loaded 31 sets in {time.time()-t0:.0f}s; base = {BASE} (read {OBS[BASE]:.6f})")

f = df.fillna(0.0)
f1v, f2v, f3v, f11v = (f[c].to_numpy() for c in ("f1", "f2", "f3", "f11"))
catsum = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()
benv = (50.0 * f["f13"] + f["f14"] + 15.0 * f["f15"] + f["f16"]).to_numpy()  # $-ised benefit burn
f5v = f["f5"].to_numpy()

# ---------------- data facts: f2 ----------------
print("\n=== f2 facts ===")
vc = df["f2"].value_counts(dropna=False).head(8)
print("f2 value counts:", dict(vc))
print(f"f2 NaN: {df['f2'].isna().sum():,}")
q_f2 = f2v >= 1
q_f2_base = q_f2 & base
print(f"f2>=1: {q_f2.sum():,} pop | in {BASE} top: {q_f2_base.sum():,}")
print(f"f2&f3 overlap in pop: {(q_f2 & (f3v>=1)).sum():,} (f3 already screened from tops)")
med = lambda m, x: float(np.median(x[m])) if m.any() else float("nan")
print(f"f2-in-top medians: catsum ${med(q_f2_base,catsum):,.0f}, f1 ${med(q_f2_base,f1v):,.0f}, "
      f"f11 {med(q_f2_base,f11v):.4f}, ben ${med(q_f2_base,benv):,.0f}")
share = [float((M[:, j] & q_f2).sum()) / TOPK for j in range(len(versions))]
print(f"f2-share across 31 tops: min {min(share):.4f} max {max(share):.4f} "
      f"(pop {q_f2.mean():.4f}) -> spread {max(share)-min(share):.4f} "
      f"{'NEVER EXCITED' if max(share)-min(share) < 0.01 else 'was excited'}")

# replacement band under f2-evict: next-best non-f2 non-f3 outsiders by base margin
k = int(q_f2_base.sum())
repl_pool = (~base) & (~q_f2) & (f3v < 1)
cand = np.where(repl_pool)[0]
repl = cand[np.argsort(-sbase[cand])[:k]]
q_repl = np.zeros(N, bool); q_repl[repl] = True
print(f"replacement band: k={k}, margin-rank span just below cutoff; "
      f"medians catsum ${med(q_repl,catsum):,.0f}, f1 ${med(q_repl,f1v):,.0f}, f11 {med(q_repl,f11v):.4f}")

# benefit + f5 pools
q_ben_top = base & (benv >= np.quantile(benv[base], 0.98))          # heaviest 2% burners in-top
q_ben_out = np.zeros(N, bool)
out_cand = np.where((~base) & (f3v < 1))[0]
q_ben_out[out_cand[np.argsort(-benv[out_cand])[:2000]]] = True      # heaviest burners outside
q_f5_out = np.zeros(N, bool)
q_f5_out[out_cand[np.argsort(-f5v[out_cand])[:2000]]] = True        # top-f5 outsiders

# ---------------- LP machinery ----------------
def lp_bounds(masks: dict[str, np.ndarray]) -> dict[str, tuple[float, float]]:
    """Sharp joint bounds. Each mask adds a refinement bit; objectives solved on shared cells."""
    key = pat.copy()
    for b, m in enumerate(masks.values()):
        key = key * 2 + m.astype(np.int64)
    cells, counts = np.unique(key, return_counts=True)
    C = len(cells)
    cell_flags = {}
    kk = cells.copy()
    for name in reversed(list(masks)):
        cell_flags[name] = (kk % 2).astype(bool); kk //= 2
    cell_pat = kk
    A = np.array([((cell_pat >> j) & 1).astype(float) for j in range(len(versions))])
    A_ub = np.vstack([A, -A])
    b_ub = np.concatenate([r + tol, -(r - tol)])
    A_eq = np.ones((1, C)); b_eq = [float(PUB)]
    bnd = list(zip(np.zeros(C), counts.astype(float)))

    def solve(c, mx=False):
        res = linprog(-c if mx else c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                      bounds=bnd, method="highs")
        assert res.status == 0, f"LP status {res.status}"
        return -res.fun if mx else res.fun

    out = {}
    for name in masks:
        c = cell_flags[name].astype(float)
        out[name] = (solve(c), solve(c, mx=True))
    # joint objective for the first two masks (in − out), if both present
    names = list(masks)
    if len(names) >= 2:
        c = cell_flags[names[0]].astype(float) - cell_flags[names[1]].astype(float)
        out["JOINT(first−second)"] = (solve(c), solve(c, mx=True))
    return out


print(f"\n=== LP bounds (31 reads, tight tol) — {time.time()-t0:.0f}s ===")
res = lp_bounds({"repl_band(in)": q_repl, "f2_in_top(out)": q_f2_base})
for name, (lo, hi) in res.items():
    print(f"{name:<24} t ∈ [{lo:7,.0f}, {hi:7,.0f}]")
lo, hi = res["JOINT(first−second)"]
print(f"\nf2-EVICT pre-registration box from the LEDGER: Δscore ∈ "
      f"[{lo/PUB:+.4f}, {hi/PUB:+.4f}]  → realized ∈ "
      f"[{OBS[BASE]+lo/PUB:.4f}, {OBS[BASE]+hi/PUB:.4f}]")
t_lo_f2, t_hi_f2 = res["f2_in_top(out)"]
print(f"f2-in-top truth-mass floor: {t_lo_f2:,.0f} "
      f"({'evict NOT refuted' if t_lo_f2 < 500 else 'CAUTION: evict guaranteed to lose ≥%.0f' % t_lo_f2})")

res2 = lp_bounds({"ben_heavy_out": q_ben_out, "ben_heavy_top": q_ben_top})
for name, (lo2, hi2) in res2.items():
    if not name.startswith("JOINT"):
        print(f"{name:<24} t ∈ [{lo2:7,.0f}, {hi2:7,.0f}]  (|Q|={int({'ben_heavy_out':q_ben_out,'ben_heavy_top':q_ben_top}[name].sum()):,})")

res3 = lp_bounds({"f5_top_out": q_f5_out})
lo3, hi3 = res3["f5_top_out"]
print(f"{'f5_top_out':<24} t ∈ [{lo3:7,.0f}, {hi3:7,.0f}]  (|Q|=2,000)")

print(f"\ndone {time.time()-t0:.0f}s")
