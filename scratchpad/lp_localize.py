"""LP miss-localization — where CAN the truth's ~8,500 uncaptured members hide?

Generalizes the f3-LP-bound trick (which v33 then measured at r≈0) to every pool at once.
The 23 scored submissions partition the 500K members into pattern cells; each public read is a
count-equation on the truth's top-100K over those cells. For each business-defined pool we ask
the LP for the MAX (and MIN) number of truth members the pool can hold OUTSIDE v29's top set —
i.e., how much of the miss set could live there under ANY truth consistent with all 23 reads.

Pools with max-slack ≈ 0  → provably not where the misses are (no candidate can win there).
Pools with big max-slack  → the only places a >0.915 candidate can hunt.

Run: .venv/bin/python scratchpad/lp_localize.py   (needs the 23-constraint tri2_cache.npz)
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from triangulate2 import OBS

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
TOL = 150  # per-read tolerance in members: LB precision (±0.0005·1e5=50) + public/full-basis wobble

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M, ids = z["M"], z["ids"]
keys = [str(x) for x in z["obs_keys"]]
assert "v33" in keys, "cache stale — need the 23-constraint build"
obs = np.array([OBS[k] for k in keys])
J, N = M.shape

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f = df.fillna(0.0)
f1, f11, f2, f3, f17 = (f[c].to_numpy() for c in ("f1", "f11", "f2", "f3", "f17"))
cat = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()
nbd = df["f6"].isna().to_numpy()
s29 = pd.read_csv(ROOT / "data" / "scores_v29.csv").set_index("id")["score"].reindex(ids).to_numpy()
m29 = np.zeros(N, bool)
m29[np.argpartition(-s29, TOPK)[:TOPK]] = True
i29 = keys.index("v29")

# pools of interest, all intersected with ~m29 (the miss set) inside the LP objective
f1cap = f1 >= np.nanmax(df["f1"].to_numpy()) - 1e-6
POOLS = {
    "never-probed (outside all 23 tops)": ~M.any(axis=0),
    "no-breakdown cohort": nbd,
    "nbd degenerate (no cat, no f1, no f4)": nbd & (f1 == 0) & df["f4"].isna().to_numpy(),
    "f3=1 (must be ~0, v33 cross-check)": f3 == 1,
    "f2=1 attrition-call pool": f2 == 1,
    "f1-at-winsor-cap": f1cap,
    "lend-line pool (f17>0 & f1>0, utilization-definable)": (f17 > 0) & (f1 > 0),
    "transactor pool (f1==0)": f1 == 0,
    "high-risk revolvers (f11>0.10 & f1>0)": (f11 > 0.10) & (f1 > 0),
    "v29 boundary band-out (rank 100-110K)": np.zeros(N, bool),  # filled below
    "everything else (none of the above)": np.zeros(N, bool),    # filled below
}
order = np.argsort(-s29)
band_out = np.zeros(N, bool)
band_out[order[TOPK:110_000]] = True
POOLS["v29 boundary band-out (rank 100-110K)"] = band_out
covered = np.zeros(N, bool)
for k, m in POOLS.items():
    if "everything else" not in k:
        covered |= m
POOLS["everything else (none of the above)"] = ~covered

# ---- build the LP over pattern-cells split by (pool crossing is handled per-objective) ----
# cells: distinct 23-bit membership patterns; per-objective we additionally split by pool&~m29.
pat = np.zeros(N, np.int64)
for j in range(J):
    pat |= M[j].astype(np.int64) << j
print(f"distinct membership patterns over {J} submissions: {len(np.unique(pat)):,}")


def bounds_for(pool_mask: np.ndarray) -> tuple[float, float]:
    """max/min truth members in (pool & ~m29), s.t. all 23 read-equations ± TOL."""
    tgt = pool_mask & ~m29
    key = pat * 2 + tgt  # split cells by objective membership
    cells, inv, counts = np.unique(key, return_inverse=True, return_counts=True)
    C = len(cells)
    # per-cell pattern bits + objective flag
    cell_pat = cells // 2
    cell_tgt = (cells % 2).astype(bool)
    A, b_lo, b_hi = [], [], []
    for j in range(J):
        row = ((cell_pat >> j) & 1).astype(float)
        A.append(row)
        b_lo.append(obs[j] * TOPK - TOL)
        b_hi.append(obs[j] * TOPK + TOL)
    A = np.array(A)
    A_ub = np.vstack([A, -A, np.ones((1, C)), -np.ones((1, C))])
    b_ub = np.concatenate([b_hi, -np.array(b_lo), [TOPK + 1], [-(TOPK - 1)]])
    c = cell_tgt.astype(float)
    ub = counts.astype(float)
    lo = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=list(zip(np.zeros(C), ub)), method="highs")
    hi = linprog(-c, A_ub=A_ub, b_ub=b_ub, bounds=list(zip(np.zeros(C), ub)), method="highs")
    assert lo.status == 0 and hi.status == 0, f"LP infeasible/failed: {lo.status}/{hi.status}"
    return lo.fun, -hi.fun


print(f"\nmiss budget: truth outside v29's top = {TOPK * (1 - OBS['v29']):,.0f} ± {TOL} members")
print(f"{'pool':<52} {'pool∩~v29':>10} {'min':>7} {'MAX':>7}")
results = {}
for name, mask in POOLS.items():
    n_out = int((mask & ~m29).sum())
    mn, mx = bounds_for(mask)
    results[name] = (n_out, mn, mx)
    print(f"{name:<52} {n_out:>10,} {mn:>7,.0f} {mx:>7,.0f}", flush=True)

pd.DataFrame([(k, *v) for k, v in results.items()],
             columns=["pool", "pool_outside_v29", "lp_min", "lp_max"]).to_csv(
    ROOT / "scratchpad" / "lp_localize_results.csv", index=False)
print("\nsaved scratchpad/lp_localize_results.csv")
print("reading: pools with MAX ≈ 0 are proven-dead hunting grounds; the miss mass must live in "
      "pools whose MAX is large — a candidate only beats 0.915 by re-ranking THOSE members.")
