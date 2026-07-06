"""tri3 stage 2 — validate the cluster-augmented family and build its posterior.

tri3_extras found: CORE + [f21p, f4p, f19z, f22r] fits all 27 exact readings at RMSE
0.0017-0.0024 (3/3 seeds; 15-term base 0.0027-0.0047) with max per-reading error ~0.003 —
threading-adjacent, where ~370K sieve formulas failed. f21p/f4p positive in 3/3 seeds;
f19z/f22r sign-unstable (correlated columns).

This script:
  A. parsimony check — CORE + [f21p, f4p] only, 3 seeds: does the stable pair carry it?
  B. posterior over CORE+4 (16 seeds, keep RMSE <= 1.5x best) -> tri3_posterior_masks.npy
     + per-term sign table + vote-gap preview vs the banked v35 set (the v41 swap pool).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triangulate2 as t2  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
K = 100_000

T, M, ids, names, keys = t2.load()
df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), ids)

g = {c: df[c].fillna(0).to_numpy(np.float64) for c in ("f4", "f19", "f21", "f22")}
new = {"f21p": t2._scale(g["f21"]), "f4p": t2._scale(g["f4"]),
       "f19z": t2._scale(g["f19"]),
       "f22r": t2._scale(pd.Series(g["f22"]).rank(pct=True).to_numpy())}
T2 = np.column_stack([T] + [new[k] for k in new]).astype(np.float32)
names2 = names + list(new)

CL4 = t2.CORE + ["f21p", "f4p", "f19z", "f22r"]
CL2 = t2.CORE + ["f21p", "f4p"]


def rmse_of(w, active):
    imp, score = t2._implied(w, T2, M, keys, names2, active, keys)
    return t2._rmse(imp), imp, score


print("=== A. parsimony: CORE + [f21p, f4p] (3 seeds) ===", flush=True)
for seed in (42, 49, 77):
    w, _ = t2.fit(T2, M, keys, keys, names2, CL2, seed=seed, maxiter=120, popsize=80)
    r, imp, _ = rmse_of(w, CL2)
    print(f"  seed {seed}: RMSE {r:.4f}  f21p {w[CL2.index('f21p')]:+.3f}  "
          f"f4p {w[CL2.index('f4p')]:+.3f}", flush=True)

print("\n=== B. posterior over CORE+4 (16 seeds) ===", flush=True)
fits = []
for sd in range(60, 76):
    w, _ = t2.fit(T2, M, keys, keys, names2, CL4, seed=sd, maxiter=110, popsize=72)
    r, imp, score = rmse_of(w, CL4)
    fits.append((w, score, r))
    print(f"  seed {sd}: RMSE {r:.4f}", flush=True)

rs = np.array([f[2] for f in fits])
keep = [f for f in fits if f[2] <= rs.min() * 1.5 + 1e-6]
print(f"kept {len(keep)}/16 (RMSE {rs.min():.4f}..{max(f[2] for f in keep):.4f})")
W = np.array([f[0] for f in keep])
print("cluster-term posterior weights (median [min..max], sign-agreement):")
for nm in ("f21p", "f4p", "f19z", "f22r", "z1", "z7", "exl", "f3neg"):
    i = CL4.index(nm)
    med = np.median(W[:, i])
    agree = (np.sign(W[:, i]) == np.sign(med)).mean() if med != 0 else 0.0
    print(f"  {nm:５<6} {med:+.3f}  [{W[:, i].min():+.3f}..{W[:, i].max():+.3f}]  sign {agree:.0%}")

masks = []
for w, score, r in keep:
    m = np.zeros(len(score), bool)
    m[np.argpartition(-score, K)[:K]] = True
    masks.append(m)
masks = np.array(masks)
np.save(ROOT / "scratchpad" / "tri3_posterior_masks.npy", masks)
print(f"saved tri3_posterior_masks.npy {masks.shape}")

# vote-gap preview vs the banked v35 set -> the v41 swap pool
s35 = pd.read_csv(ROOT / "data" / "scores_v35.csv").set_index("id")["score"].reindex(ids).to_numpy()
S = np.zeros(len(s35), bool)
S[np.argpartition(-s35, K)[:K]] = True
vote = masks.sum(axis=0).astype(np.float64)
Kc = masks.shape[0]
f3 = df["f3"].fillna(0).to_numpy()
whale = M.all(axis=0)
in_pool = np.flatnonzero(~S & (f3 == 0))
out_pool = np.flatnonzero(S & ~whale)
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = [names.index(n) for n in ("z1", "z7", "z9", "z10", "exl", "f3neg")]
tb = (T[:, SIX].astype(np.float64)) @ w6
tb = tb / tb.std()
in_pool = in_pool[np.lexsort((-tb[in_pool], -vote[in_pool]))]
out_pool = out_pool[np.lexsort((tb[out_pool], vote[out_pool]))]
gaps = (vote[in_pool[:8000]] - vote[out_pool[:8000]]) / Kc
print("\nv41 conviction curve (cluster-posterior vote-gap vs v35 set):")
for n in (300, 600, 1000, 1500, 2500, 4000, 6000, 8000):
    if n <= len(gaps):
        print(f"  N={n:>5}: gap@N {gaps[n-1]:+.2f}")
e35 = np.mean([(S & m).sum() / K for m in masks])
print(f"E[LB | cluster-posterior] for v35's set: {e35:.3f} (actual 0.918971)")
f21v = g["f21"]
print(f"swap-IN preview at N=1500: f21 med {np.median(f21v[in_pool[:1500]]):,.0f}  "
      f"f4 med {np.median(g['f4'][in_pool[:1500]]):,.0f}  "
      f"vote med {np.median(vote[in_pool[:1500]]):.0f}/{Kc}")
