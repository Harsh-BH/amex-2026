"""Generator sieve v2 — concave-transform grammar (the compression hypothesis).

v1 result: NO pure raw-dollar formula threads the 27 exact counts (best maxsc 2.92,
rmse 0.0059, worse than the z-family's 0.0037), with 96% of top candidates piled at the
lodging grid edge — a mis-specification signature. Both refit26/27 core fits carry large,
sign-unstable rank-basis mass -> the truth likely compresses its engines concavely.

v2 grammar: score = sum_c m_c*Ts(spend_c) + y*T1(f1) - L*f11*E(f1) [+ sides, stage 2]
  T1 in {dollar, sqrt, log1p, rank}   (revolve-balance engine transform)
  Ts in {dollar, sqrt, rank}          (all spend categories jointly)
  E  in {dollar f1, T1(f1)}           (expected-loss exposure basis)
Every transformed column is rescaled to the dollar column's mean, so rate grids keep
their per-$ meaning across cells. f3 hard evict always. Sides (stage 2) as in v1.
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
cache_ids = z["ids"]
obs_v = np.array([OBS[k] for k in keys])
tol_v = np.array([0.0025 if k in EXACT6 else 0.003 for k in keys])

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), cache_ids)

SPEND = ["f6", "f7", "f8", "f9", "f10"]
raw = {c: df[c].fillna(0).to_numpy(np.float64) for c in SPEND + ["f1", "f2", "f3", "f11",
                                                                "f13", "f14", "f15", "f16",
                                                                "f19", "f20"]}
catsum = sum(raw[c] for c in SPEND)
f21_0 = df["f21"].fillna(0).to_numpy(np.float64)
f4_0 = df["f4"].fillna(0).to_numpy(np.float64)
f21_m = df["f21"].fillna(df["f21"].median()).to_numpy(np.float64)
f4_m = df["f4"].fillna(df["f4"].median()).to_numpy(np.float64)
BEN = 50.0 * raw["f13"] + raw["f14"] + 15.0 * raw["f15"] + raw["f16"]


def rescale(t: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Match the dollar column's mean so rate grids keep per-$ meaning."""
    return t * (ref.mean() / (t.mean() + 1e-12))


def pct(v: np.ndarray) -> np.ndarray:
    return pd.Series(v).rank(pct=True).to_numpy(np.float64)


def t_variants(x: np.ndarray) -> dict[str, np.ndarray]:
    xc = np.clip(x, 0, None)
    return {"dol": x,
            "sqrt": rescale(np.sqrt(xc) * np.sign(x), x) if (x < 0).any() else rescale(np.sqrt(xc), x),
            "log": rescale(np.log1p(xc), x),
            "rank": rescale(pct(x), x)}


T1V = t_variants(raw["f1"])                      # dollar/sqrt/log/rank on the balance engine
TSV = {form: {c: t_variants(raw[c])[form] for c in SPEND} for form in ("dol", "sqrt", "rank")}

G_A6 = [-0.01, 0.0, 0.01]
G_A8 = [0.0, 0.015]
G_A9 = [0.0, 0.045, 0.085, 0.14, 0.22]
G_A10 = [0.0, 0.01, 0.03]
G_Y = [0.12, 0.16, 0.20, 0.26, 0.32]
G_L = [0.6, 0.9, 1.2, 1.6]
G_KAP = [0.0, 0.2]
G_T1 = ["dol", "sqrt", "log", "rank"]
G_TS = ["dol", "sqrt", "rank"]
G_EB = [0, 1]                                    # EL exposure: 0 = dollar f1, 1 = T1(f1)

G_S19 = [0.0, 100.0, 300.0, 700.0]
G_S20 = [0.0, 150.0, 400.0]
G_RW = [(0.0, 0.0), (0.011, 0.0), (0.015, 0.0), (0.011, 0.0105)]
G_BN = [0.0, 1.0]
G_P2 = [0.0, -150.0, -600.0]

PARAM_KEYS = ["t1", "ts", "eb", "a6", "a8", "a9", "a10", "y", "L", "kap",
              "s19", "s20", "rw", "rf4", "bn", "p2", "imp"]
N_EVAL = 0
t0 = time.time()
rows = []


def evaluate(t1, ts, eb, a6, a8, a9, a10, y, L, kap,
             s19=0.0, s20=0.0, rw=0.0, rf4=0.0, bn=0.0, p2=0.0, imp=0):
    global N_EVAL
    N_EVAL += 1
    sp = TSV[ts]
    exposure = raw["f1"] if eb == 0 else T1V[t1]
    s = (0.013 * sp["f7"] + a6 * sp["f6"] + a8 * sp["f8"] + a9 * sp["f9"] + a10 * sp["f10"]
         + y * T1V[t1] - L * raw["f11"] * (exposure + kap * catsum)
         + s19 * raw["f19"] + s20 * raw["f20"]
         - rw * (f21_0 if imp == 0 else f21_m) - rf4 * (f4_0 if imp == 0 else f4_m)
         - bn * BEN + p2 * raw["f2"] - 1e9 * raw["f3"]).astype(np.float32)
    idx = np.argpartition(-s, K)[:K]
    ov = M[:, idx].sum(axis=1) / K
    err = ov - obs_v
    ms = float(np.abs(err / tol_v).max())
    rows.append((ms, float(np.sqrt((err ** 2).mean())), float(np.abs(err).max()),
                 t1, ts, eb, a6, a8, a9, a10, y, L, kap, s19, s20, rw, rf4, bn, p2, imp))
    if N_EVAL % 10000 == 0:
        print(f"  {N_EVAL:,} evals, {N_EVAL / (time.time() - t0):.0f}/s, "
              f"best {min(r[0] for r in rows):.2f}", flush=True)
    return ov


def side_grid():
    for s19, s20, (rw, rf4), bn, p2 in itertools.product(G_S19, G_S20, G_RW, G_BN, G_P2):
        for imp in ((0,) if (rw == 0 and rf4 == 0) else (0, 1)):
            yield s19, s20, rw, rf4, bn, p2, imp


print("=== stage 1: structural cells x core rates ===", flush=True)
for t1, ts, eb in itertools.product(G_T1, G_TS, G_EB):
    if eb == 1 and t1 == "dol":
        continue                                 # duplicate of eb=0
    for a6, a8, a9, a10, y, L, kap in itertools.product(G_A6, G_A8, G_A9, G_A10, G_Y, G_L, G_KAP):
        evaluate(t1, ts, eb, a6, a8, a9, a10, y, L, kap)

rows.sort(key=lambda r: r[0])
print(f"stage 1 best maxsc {rows[0][0]:.2f} rmse {rows[0][1]:.4f} "
      f"({rows[0][3]}/{rows[0][4]}/eb{rows[0][5]})", flush=True)

cores, seen = [], set()
for r in rows:
    core = r[3:13]
    if core not in seen:
        seen.add(core)
        cores.append(core)
    if len(cores) >= 100:
        break

print("=== stage 2: top-100 cores x side grid ===", flush=True)
for core in cores:
    for s in side_grid():
        evaluate(*core, *s)

rows.sort(key=lambda r: r[0])
out = pd.DataFrame(rows[:3000], columns=["maxsc", "rmse", "maxerr"] + PARAM_KEYS)
out.to_csv(ROOT / "scratchpad" / "sieve2_results.csv", index=False)

print(f"\n=== DONE: {N_EVAL:,} evals in {(time.time() - t0) / 60:.1f} min ===")
print(f"THREADING candidates (maxsc<=1): {int((out.maxsc <= 1).sum())}")
print("\ntop 12:")
print(out.head(12).to_string(index=False))
print("\nbest per structural cell (t1/ts/eb):")
print(out.groupby(["t1", "ts", "eb"]).maxsc.min().sort_values().head(10).to_string())

v35_mask = M[keys.index("v35")]
print("\nper-reading errors, top 3:")
for _, r in out.head(3).iterrows():
    p = {k: r[k] for k in PARAM_KEYS}
    p["eb"], p["imp"] = int(p["eb"]), int(p["imp"])
    ov = evaluate(**p)
    rows.pop()
    print(json.dumps({k: (v if isinstance(v, str) else round(float(v), 4)) for k, v in p.items()}),
          f" maxsc {r.maxsc:.2f} rmse {r.rmse:.4f}")
    print("   " + "  ".join(f"{k}{(o - OBS[k]) * 1000:+.1f}" for k, o in zip(keys, ov)))
