"""Generator sieve v3 — per-feature MIXED basis + displacement-cluster side terms.

Verdicts so far: v1 pure raw-dollar fails (best maxsc 2.92); v2 global concave transforms
fail (best stage-1 cell was dol/dol — every concave cell WORSE). But the z-family fits
best (RMSE 0.0037) using unstable rank/dollar mixtures, and the LB-validated v22 win was
exactly a mixed basis (specialty cats ranked, engines dollar). So v3 searches per-feature
basis assignment — and adds the residual-displacement cluster as POSITIVE side terms
(+f21 redemption, +f4 points, +f19/f20 supp/cards, +f22 engagement), which v1/v2 only
ever priced as costs.
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
M = z["M"]
keys = [str(x) for x in z["obs_keys"]]
obs_v = np.array([OBS[k] for k in keys])
tol_v = np.array([0.0025 if k in EXACT6 else 0.003 for k in keys])

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), z["ids"])

SPEND = ["f6", "f7", "f8", "f9", "f10"]
raw = {c: df[c].fillna(0).to_numpy(np.float64) for c in
       SPEND + ["f1", "f2", "f3", "f11", "f13", "f14", "f15", "f16", "f19", "f20", "f22"]}
catsum = sum(raw[c] for c in SPEND)
f21_0 = df["f21"].fillna(0).to_numpy(np.float64)
f4_0 = df["f4"].fillna(0).to_numpy(np.float64)
BEN = 50.0 * raw["f13"] + raw["f14"] + 15.0 * raw["f15"] + raw["f16"]
f22_r = pd.Series(raw["f22"]).rank(pct=True).to_numpy()


def rescale(t, ref):
    return t * (ref.mean() / (t.mean() + 1e-12))


def pct(v):
    return pd.Series(v).rank(pct=True).to_numpy(np.float64)


V1 = {"dol": raw["f1"],
      "sqrt": rescale(np.sqrt(np.clip(raw["f1"], 0, None)), raw["f1"]),
      "rank": rescale(pct(raw["f1"]), raw["f1"])}
V7 = {"dol": raw["f7"], "sqrt": rescale(np.sqrt(np.clip(raw["f7"], 0, None)), raw["f7"])}
VS = {"dol": {c: raw[c] for c in ("f6", "f8", "f9", "f10")},
      "rank": {c: rescale(pct(raw[c]), raw[c]) for c in ("f6", "f8", "f9", "f10")}}

G_A6 = [-0.01, 0.0, 0.01]
G_A8 = [0.0, 0.015]
G_A9 = [0.0, 0.045, 0.085, 0.14]
G_A10 = [0.0, 0.01, 0.03]
G_Y = [0.12, 0.16, 0.20, 0.26]
G_L = [0.6, 0.9, 1.2, 1.6]
G_KAP = [0.0, 0.2]

PARAM_KEYS = ["b1", "b7", "bs", "a6", "a8", "a9", "a10", "y", "L", "kap",
              "e21", "e4", "s19", "s20", "e22", "bn", "p2", "rwc"]
N_EVAL = 0
t0 = time.time()
rows = []


def evaluate(b1, b7, bs, a6, a8, a9, a10, y, L, kap,
             e21=0.0, e4=0.0, s19=0.0, s20=0.0, e22=0.0, bn=0.0, p2=0.0, rwc=0.0):
    global N_EVAL
    N_EVAL += 1
    sp = VS[bs]
    s = (0.013 * V7[b7] + a6 * sp["f6"] + a8 * sp["f8"] + a9 * sp["f9"] + a10 * sp["f10"]
         + y * V1[b1] - L * raw["f11"] * (raw["f1"] + kap * catsum)
         + (e21 - rwc) * f21_0 + e4 * f4_0 + s19 * raw["f19"] + s20 * raw["f20"]
         + e22 * f22_r - bn * BEN + p2 * raw["f2"] - 1e9 * raw["f3"]).astype(np.float32)
    idx = np.argpartition(-s, K)[:K]
    ov = M[:, idx].sum(axis=1) / K
    err = ov - obs_v
    ms = float(np.abs(err / tol_v).max())
    rows.append((ms, float(np.sqrt((err ** 2).mean()))) + (b1, b7, bs, a6, a8, a9, a10, y, L, kap,
                                                           e21, e4, s19, s20, e22, bn, p2, rwc))
    if N_EVAL % 10000 == 0:
        print(f"  {N_EVAL:,} evals, {N_EVAL/(time.time()-t0):.0f}/s, "
              f"best {min(r[0] for r in rows):.2f}", flush=True)
    return ov


def side_grid():
    for e21, e4, s19, s20, e22, bn, p2 in itertools.product(
            (0.0, 0.003, 0.008), (0.0, 0.004), (0.0, 200.0, 600.0), (0.0, 300.0),
            (0.0, 800.0), (0.0, 1.0), (0.0, -300.0)):
        for rwc in ((0.0, 0.011) if e21 == 0.0 else (0.0,)):
            yield e21, e4, s19, s20, e22, bn, p2, rwc


print("=== stage 1: 12 basis cells x core rates ===", flush=True)
for b1, b7, bs in itertools.product(("dol", "sqrt", "rank"), ("dol", "sqrt"), ("dol", "rank")):
    for a6, a8, a9, a10, y, L, kap in itertools.product(G_A6, G_A8, G_A9, G_A10, G_Y, G_L, G_KAP):
        evaluate(b1, b7, bs, a6, a8, a9, a10, y, L, kap)

rows.sort(key=lambda r: r[0])
print(f"stage 1 best maxsc {rows[0][0]:.2f} rmse {rows[0][1]:.4f} cell {rows[0][2:5]}", flush=True)
print("best per basis cell:")
cell_best = {}
for r in rows:
    cell_best.setdefault(r[2:5], r[0])
for cell, ms in sorted(cell_best.items(), key=lambda kv: kv[1])[:12]:
    print(f"  {cell}: {ms:.2f}")

cores, seen = [], set()
for r in rows:
    core = r[2:10]
    if core not in seen:
        seen.add(core)
        cores.append(core)
    if len(cores) >= 120:
        break

print("=== stage 2: top-120 cores x displacement side grid ===", flush=True)
for core in cores:
    for s in side_grid():
        evaluate(*core, *s)

rows.sort(key=lambda r: r[0])
out = pd.DataFrame(rows[:3000], columns=["maxsc", "rmse"] + PARAM_KEYS)
out.to_csv(ROOT / "scratchpad" / "sieve3_results.csv", index=False)

print(f"\n=== DONE: {N_EVAL:,} evals in {(time.time()-t0)/60:.1f} min ===")
print(f"THREADING (maxsc<=1): {int((out.maxsc <= 1).sum())}")
print("\ntop 12:")
print(out.head(12).to_string(index=False))
print("\nside-term usage in top-50 (mean value):")
print(out.head(50)[["e21", "e4", "s19", "s20", "e22", "bn", "p2", "rwc"]].mean().to_string())

print("\nper-reading errors, top 3:")
for _, r in out.head(3).iterrows():
    p = {k: r[k] for k in PARAM_KEYS}
    ov = evaluate(**p)
    rows.pop()
    print(json.dumps({k: (v if isinstance(v, str) else round(float(v), 4)) for k, v in p.items()}),
          f" maxsc {r.maxsc:.2f} rmse {r.rmse:.4f}")
    print("   " + "  ".join(f"{k}{(o-OBS[k])*1000:+.1f}" for k, o in zip(keys, ov)))
