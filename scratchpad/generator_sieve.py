"""Generator sieve — exact-count feasibility search over raw-dollar business-formula space.

Different in kind from triangulate2's DE fit: instead of continuous weights over a fixed
z-scaled basis minimizing smooth RMSE, enumerate DISCRETE business formulas (raw-dollar P&L
grammar x imputation policy x round rates) and accept only candidates whose 27 implied
readings thread every exact public count within tolerance.

Acceptance: reading noise sigma ~ 0.001 (70/30 split, A42) -> tol 0.0025 on the four exact
6-dp readings, 0.003 on the 3-dp ones. The current 15-term family fails this by up to
+-0.010 (refit27), so the sieve is sharp: a wrong form threads 27 windows with p ~ 1e-14.

Stages: 1) core-economics grid (17,280) with side terms 0;  1b) side-term sweep on a
fit6-anchored core (insurance in case big side terms make good cores rank badly alone);
2) top-250 cores x side grid (504);  3) local refinement of top-50.

score = 0.013*f7 + a6*f6 + a8*f8 + a9*f9 + a10*f10            [interchange margins, $/$]
      + y*f1                                                   [net yield on revolve bal]
      - L*(f11*f1 + kappa*f11*catsum)                          [expected loss on exposure]
      + s19*f19 + s20*f20                                      [supp/card fee revenue, $]
      - rw*f21 - rf4*f4                                        [rewards cost, per point]
      - bn*(50*f13 + f14 + 15*f15 + f16)                       [benefit credits, $-ised]
      + p2*f2                                                  [servicing/attrition calls]
      - 1e9*f3                                                 [hard evict, triple-validated]
m7 fixed at 0.013 $/$ as numeraire (ranking depends on ratios only; f7 sign-stable +).
Missing: spend/f1/f11/benefits/f2 -> 0; f4/f21 -> policy {0, median} (the rewards cohort
is 51.4% of pop and was never probed as a regime).

ponytail: single process, argpartition per candidate (~10ms) — 150K evals ~ 30 min. Batch
tricks only if this measurably fails.
"""
import itertools
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
K = 100_000

OBS = {"v1": .449, "v2": .465, "v3": .614, "v4": .609, "v5": .733, "v6": .675, "v7": .768,
       "v8": .681, "v9": .727, "v10": .805, "v11min": .823, "v15": .827, "v19": .859,
       "v21": .851, "v22": .866, "v24": .880, "v25": .866, "v26": .843, "v27": .895,
       "v29": .915, "v30": .904, "v32": .912, "v33": .907, "v34": .917614,
       "v35": .918971, "v37L": .919143, "v36": .917386}
EXACT6 = {"v34", "v35", "v37L", "v36"}

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
Tz, M = z["T"], z["M"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
cache_ids = z["ids"]
assert M.shape == (27, 500_000)
obs_v = np.array([OBS[k] for k in keys])
tol_v = np.array([0.0025 if k in EXACT6 else 0.003 for k in keys])

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), cache_ids), "row order mismatch vs cache"

f = {c: df[c].fillna(0).to_numpy(np.float64) for c in
     ["f1", "f2", "f3", "f6", "f7", "f8", "f9", "f10", "f11",
      "f13", "f14", "f15", "f16", "f19", "f20"]}
catsum = f["f6"] + f["f7"] + f["f8"] + f["f9"] + f["f10"]
f21_0 = df["f21"].fillna(0).to_numpy(np.float64)
f4_0 = df["f4"].fillna(0).to_numpy(np.float64)
f21_m = df["f21"].fillna(df["f21"].median()).to_numpy(np.float64)
f4_m = df["f4"].fillna(df["f4"].median()).to_numpy(np.float64)
BEN = 50.0 * f["f13"] + f["f14"] + 15.0 * f["f15"] + f["f16"]

COLS = ["f6", "f7", "f8", "f9", "f10", "f1", "exl1", "exlC", "f19", "f20",
        "f21_0", "f21_m", "f4_0", "f4_m", "BEN", "f2", "f3"]
TERMS = np.column_stack([
    f["f6"], f["f7"], f["f8"], f["f9"], f["f10"], f["f1"],
    f["f11"] * f["f1"], f["f11"] * catsum, f["f19"], f["f20"],
    f21_0, f21_m, f4_0, f4_m, BEN, f["f2"], f["f3"],
]).astype(np.float32)
TERMS = np.ascontiguousarray(TERMS)

N_EVAL = 0


def implied(w: np.ndarray) -> np.ndarray:
    """27 implied readings for a raw-dollar weight vector over COLS."""
    global N_EVAL
    N_EVAL += 1
    s = TERMS @ w.astype(np.float32)
    idx = np.argpartition(-s, K)[:K]
    return M[:, idx].sum(axis=1) / K


def wvec(a6, a8, a9, a10, y, L, kap, s19=0.0, s20=0.0, rw=0.0, rf4=0.0,
         bn=0.0, p2=0.0, imp=0) -> np.ndarray:
    w = np.zeros(len(COLS))
    w[0], w[1], w[2], w[3], w[4] = a6, 0.013, a8, a9, a10
    w[5] = y
    w[6] = -L
    w[7] = -L * kap
    w[8], w[9] = s19, s20
    w[10 + imp] = -rw          # f21_0 or f21_m
    w[12 + imp] = -rf4         # f4_0 or f4_m
    w[14] = -bn
    w[15] = p2
    w[16] = -1e9               # f3 hard evict
    return w


def stats(ov: np.ndarray):
    err = ov - obs_v
    return float(np.abs(err / tol_v).max()), float(np.sqrt((err ** 2).mean())), float(np.abs(err).max())


# ---- controls: harness must reproduce the known family errors ----
w15 = np.load(ROOT / "scratchpad" / "tri2_core_w.npy")
s15 = Tz[:, :15] @ w15.astype(np.float32)
idx15 = np.argpartition(-s15, K)[:K]
ms, rmse, mx = stats(M[:, idx15].sum(axis=1) / K)
print(f"CONTROL core15 : maxerr_scaled {ms:.2f}  rmse {rmse:.4f}  maxerr {mx:.4f} (expect rmse ~0.0037)")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = [names.index(n) for n in ("z1", "z7", "z9", "z10", "exl", "f3neg")]
s6 = Tz[:, SIX] @ w6.astype(np.float32)
idx6 = np.argpartition(-s6, K)[:K]
ms, rmse, mx = stats(M[:, idx6].sum(axis=1) / K)
print(f"CONTROL fit6   : maxerr_scaled {ms:.2f}  rmse {rmse:.4f}  maxerr {mx:.4f} (expect rmse ~0.0064)", flush=True)

# ---- grids ----
G_A6 = [-0.02, -0.01, 0.0, 0.01, 0.02]
G_A8 = [0.0, 0.01, 0.02]
G_A9 = [0.0, 0.02, 0.045, 0.085]
G_A10 = [0.0, 0.01, 0.02, 0.04]
G_Y = [0.06, 0.09, 0.12, 0.156, 0.20, 0.24]
G_L = [0.35, 0.6, 0.85, 1.15]
G_KAP = [0.0, 0.15, 0.3]

G_S19 = [0.0, 100.0, 300.0, 700.0]
G_S20 = [0.0, 150.0, 400.0]
G_RW = [(0.0, 0.0), (0.011, 0.0), (0.015, 0.0), (0.011, 0.0105)]
G_BN = [0.0, 1.0]
G_P2 = [0.0, -150.0, -600.0]

PARAM_KEYS = ["a6", "a8", "a9", "a10", "y", "L", "kap", "s19", "s20", "rw", "rf4", "bn", "p2", "imp"]


def side_grid():
    for s19, s20, (rw, rf4), bn, p2 in itertools.product(G_S19, G_S20, G_RW, G_BN, G_P2):
        imps = (0,) if (rw == 0 and rf4 == 0) else (0, 1)
        for imp in imps:
            yield s19, s20, rw, rf4, bn, p2, imp


t0 = time.time()
rows = []


def run(params):
    ms, rmse, mx = stats(implied(wvec(*params[:7], *params[7:])))
    rows.append((ms, rmse, mx) + tuple(params))
    if N_EVAL % 5000 == 0:
        print(f"  {N_EVAL:,} evals, {N_EVAL / (time.time() - t0):.0f}/s, "
              f"best so far {min(r[0] for r in rows):.2f}", flush=True)


print("=== stage 1: core economics grid ===", flush=True)
for a6, a8, a9, a10, y, L, kap in itertools.product(G_A6, G_A8, G_A9, G_A10, G_Y, G_L, G_KAP):
    run((a6, a8, a9, a10, y, L, kap, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0))

print("=== stage 1b: side sweep on fit6-anchored core ===", flush=True)
ANCHOR = (0.0, 0.01, 0.045, 0.01, 0.156, 0.85, 0.15)
for s19, s20, rw, rf4, bn, p2, imp in side_grid():
    run(ANCHOR + (s19, s20, rw, rf4, bn, p2, imp))

rows.sort(key=lambda r: r[0])
core_seen, cores = set(), []
for r in rows:
    core = r[3:10]
    if core not in core_seen:
        core_seen.add(core)
        cores.append(core)
    if len(cores) >= 250:
        break
print(f"stage 1 best maxerr_scaled {rows[0][0]:.2f} rmse {rows[0][1]:.4f}; "
      f"{len(cores)} distinct cores -> stage 2", flush=True)

print("=== stage 2: top cores x side grid ===", flush=True)
for core in cores:
    for s19, s20, rw, rf4, bn, p2, imp in side_grid():
        run(core + (s19, s20, rw, rf4, bn, p2, imp))

rows.sort(key=lambda r: r[0])
print(f"stage 2 best maxerr_scaled {rows[0][0]:.2f} rmse {rows[0][1]:.4f}", flush=True)

print("=== stage 3: local refinement of top 50 ===", flush=True)
seen = set()
finalists = []
for r in rows[:200]:
    p = r[3:]
    if p[:7] + p[7:] not in seen:
        seen.add(p)
        finalists.append(p)
    if len(finalists) >= 50:
        break
for p in finalists:
    a6, a8, a9, a10, y, L, kap = p[:7]
    side = p[7:]
    for dy, dL, dk, d9 in itertools.product((-0.015, 0.0, 0.015), (-0.125, 0.0, 0.125),
                                            (-0.075, 0.0, 0.075), (-0.01, 0.0, 0.01)):
        if dy == dL == dk == d9 == 0.0:
            continue
        run((a6, a8, max(a9 + d9, 0.0), a10, max(y + dy, 0.01),
             max(L + dL, 0.05), max(kap + dk, 0.0)) + side)

rows.sort(key=lambda r: r[0])
out = pd.DataFrame(rows[:2000], columns=["maxerr_scaled", "rmse", "maxerr"] + PARAM_KEYS)
out.to_csv(ROOT / "scratchpad" / "sieve_results.csv", index=False)

print(f"\n=== DONE: {N_EVAL:,} evals in {(time.time() - t0) / 60:.1f} min ===")
thread = out[out.maxerr_scaled <= 1.0]
print(f"THREADING candidates (all 27 within tol): {len(thread)}")
print("\ntop 15 by max scaled violation:")
print(out.head(15).to_string(index=False))

# grid-edge pile-up warning
top = out.head(50)
for col, hi in (("y", max(G_Y)), ("a9", max(G_A9)), ("L", max(G_L)), ("s19", max(G_S19))):
    share = float((top[col] >= hi - 1e-9).mean())
    if share > 0.4:
        print(f"WARNING: {share:.0%} of top-50 at {col} grid edge {hi} — expand the grid outward.")

# per-reading detail for the top 5 + overlap vs the banked v35 set
print("\nper-reading errors, top 5:")
v35_mask = M[keys.index("v35")]
for _, r in out.head(5).iterrows():
    p = [r[k] for k in PARAM_KEYS]
    p[-1] = int(p[-1])
    ov = implied(wvec(*p[:7], *p[7:]))
    s = TERMS @ wvec(*p[:7], *p[7:]).astype(np.float32)
    tidx = np.argpartition(-s, K)[:K]
    ov35 = v35_mask[tidx].sum() / K
    print(json.dumps({k: round(float(v), 4) for k, v in zip(PARAM_KEYS, p)}),
          f" maxsc {r.maxerr_scaled:.2f} rmse {r.rmse:.4f} | overlap vs v35 set {ov35:.3f}")
    print("   " + "  ".join(f"{k}{(o - OBS[k]) * 1000:+.1f}" for k, o in zip(keys, ov)))
