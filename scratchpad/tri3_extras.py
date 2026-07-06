"""tri3 extras — family-side test of the displacement-cluster terms at all 27 constraints.

The displacement fitter (residual_displacement.py) found the f21/f4/f19/f22 relationship
cluster as the top residual direction, and the design-coverage audit (A43) showed these
directions were never excited by any probe — so triangulate2's original extras test never
had power on them, and several (f19z, f20z, f22-rank, f23-rank, positive f21/f4 on the
0-filled dollar basis, regime intercepts) were never candidates at all.

This reruns the greedy-extra test with those terms, on all 27 constraints, 2 seeds each,
plus one JOINT cluster fit. Uses triangulate2's own fit machinery (same DE, same weights,
same OBS_POW) so numbers are apples-to-apples with refit27 (core RMSE ~0.0037).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triangulate2 as t2  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

T, M, ids, names, keys = t2.load()
df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), ids)

g = {c: df[c].fillna(0).to_numpy(np.float64) for c in ("f4", "f19", "f20", "f21", "f22", "f23")}
new = {
    "f21p": t2._scale(g["f21"]),                          # redemption flow, 0-filled dollar basis
    "f4p": t2._scale(g["f4"]),                            # points stock
    "f19z": t2._scale(g["f19"]),                          # supp accounts
    "f20z": t2._scale(g["f20"]),                          # active charge cards
    "f22r": t2._scale(pd.Series(g["f22"]).rank(pct=True).to_numpy()),
    "f23r": t2._scale(pd.Series(g["f23"]).rank(pct=True).to_numpy()),
    "mrew": t2._scale(df["f4"].isna().to_numpy(float)),   # rewards-inactive regime intercept
    "mline": t2._scale(df["f17"].isna().to_numpy(float)),  # no-lend-line regime intercept
    "supb": t2._scale(g["f19"] + 0.5 * g["f20"]),
}
T2 = np.column_stack([T] + [new[k] for k in new]).astype(np.float32)
names2 = names + list(new)
print(f"T2 {T2.shape}; testing {list(new)}", flush=True)


def rmse_of(w, active):
    imp, _ = t2._implied(w, T2, M, keys, names2, active, keys)
    return t2._rmse(imp), imp


base = {}
for seed in (42, 49):
    w, _ = t2.fit(T2, M, keys, keys, names2, t2.CORE, seed=seed, maxiter=100, popsize=64)
    base[seed], _ = rmse_of(w, t2.CORE)
    print(f"BASE core15 seed {seed}: RMSE {base[seed]:.4f}", flush=True)

print("\n--- greedy extras (delta vs same-seed base; meaningful if <= -0.0008 on BOTH) ---",
      flush=True)
for e in new:
    deltas = []
    for seed in (42, 49):
        cols = t2.CORE + [e]
        w, _ = t2.fit(T2, M, keys, keys, names2, cols, seed=seed, maxiter=100, popsize=64)
        r, _ = rmse_of(w, cols)
        deltas.append((r - base[seed], float(w[cols.index(e)])))
    print(f"  +{e:5} " + "  ".join(f"seed{s}: d{d:+.4f} w{wt:+.3f}" for s, (d, wt)
                                   in zip((42, 49), deltas)), flush=True)

print("\n--- joint cluster fit: CORE + [f21p, f4p, f19z, f22r] ---", flush=True)
cols = t2.CORE + ["f21p", "f4p", "f19z", "f22r"]
for seed in (42, 49, 77):
    w, _ = t2.fit(T2, M, keys, keys, names2, cols, seed=seed, maxiter=120, popsize=80)
    r, imp = rmse_of(w, cols)
    wt = {n: round(float(w[cols.index(n)]), 3) for n in ("f21p", "f4p", "f19z", "f22r")}
    print(f"  seed {seed}: RMSE {r:.4f} (base {base.get(seed, min(base.values())):.4f})  {wt}",
          flush=True)
    if seed == 42:
        for k in keys:
            print(f"    {k:>6}: fit {imp[k]:.3f} actual {t2.OBS[k]:.3f} err {imp[k]-t2.OBS[k]:+.3f}")
