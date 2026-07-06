"""Displacement robustness suite — is the f21/relationship-cluster displacement REAL?

Candidate-B go/no-go. Tests the residual-displacement lead (f21+ at 21.9% SS-reduction,
borderline vs null 95th=22.0%) four ways:
  1. ERA STABILITY: rerun the fitter against 4 independent-era truth fits
     (current 27-constraint, v37L_frozen 26, v35_frozen 25, v34_frozen 24) — a real
     displacement should top the list in every era; a noise artifact should not.
  2. JACKKNIFE: drop each of the 27 readings; does f21+/cluster stay top-3? Explicitly
     report drop-v21 and drop-v6 (the two historical f4-informative reads).
  3. BLEND vs SINGLE: does the coherent cluster blend (f21,f4,f19+.5f20,f22) beat f21?
  4. PERMUTATION NULL per era (200 perms).
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
K = 100_000
Q = 2_000
RNG = np.random.default_rng(11)

OBS = {"v1": .449, "v2": .465, "v3": .614, "v4": .609, "v5": .733, "v6": .675, "v7": .768,
       "v8": .681, "v9": .727, "v10": .805, "v11min": .823, "v15": .827, "v19": .859,
       "v21": .851, "v22": .866, "v24": .880, "v25": .866, "v26": .843, "v27": .895,
       "v29": .915, "v30": .904, "v32": .912, "v33": .907, "v34": .917614,
       "v35": .918971, "v37L": .919143, "v36": .917386}

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
Tz, M = z["T"], z["M"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
obs_v = np.array([OBS[k] for k in keys])

w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = [names.index(n) for n in ("z1", "z7", "z9", "z10", "exl", "f3neg")]
margin_r = pd.Series((Tz[:, SIX] @ w6.astype(np.float32)).astype(np.float64)).rank(pct=True).to_numpy()

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), z["ids"])
SPEND = ["f6", "f7", "f8", "f9", "f10"]
g = {c: df[c].fillna(0).to_numpy(np.float64) for c in [f"f{i}" for i in range(1, 24)]}
catsum = sum(g[c] for c in SPEND)

D: dict[str, np.ndarray] = {f"f{i}": g[f"f{i}"] for i in range(1, 24)}
D["miss_rew"] = df["f4"].isna().to_numpy(float)
D["miss_line"] = df["f17"].isna().to_numpy(float)
D["miss_nbd"] = df["f6"].isna().to_numpy(float)
D["sqrt_f1"] = np.sqrt(np.clip(g["f1"], 0, None))
D["log_cat"] = np.log1p(np.clip(catsum, 0, None))
for c in SPEND:
    D[f"share_{c}"] = g[c] / (catsum + 1.0)
D["exl"] = g["f11"] * g["f1"]
D["f11cat"] = g["f11"] * catsum
D["dualish"] = pd.Series(catsum).rank(pct=True).to_numpy() * (g["f1"] > 0)
D["redeem_rate"] = g["f21"] / (g["f4"] + 1.0)
D["ben"] = 50 * g["f13"] + g["f14"] + 15 * g["f15"] + g["f16"]
D["util"] = np.where(g["f17"] > 0, g["f1"] / np.maximum(g["f17"], 1.0), 0.0)
D["supp_blend"] = g["f19"] + 0.5 * g["f20"]
D["engage"] = (pd.Series(g["f12"]).rank(pct=True) + pd.Series(g["f22"]).rank(pct=True)).to_numpy()
pr = {k: pd.Series(v).rank(pct=True).to_numpy() for k, v in
      (("f21", g["f21"]), ("f4", g["f4"]), ("sb", D["supp_blend"]), ("f22", g["f22"]))}
D["cluster_blend"] = (pr["f21"] + pr["f4"] + pr["sb"] + pr["f22"]) / 4.0

HR = {name: pd.Series(h).rank(pct=True).to_numpy() + 1e-6 * margin_r for name, h in D.items()}

BASES = [("current-27", ROOT / "scratchpad" / "tri2_core_w.npy"),
         ("v37L-era-26", ROOT / "scratchpad" / "v37L_frozen" / "tri2_core_w.npy"),
         ("v35-era-25", ROOT / "scratchpad" / "v35_frozen" / "tri2_core_w.npy"),
         ("v34-era-24", ROOT / "scratchpad" / "v34_frozen" / "tri2_core_w.npy")]


def build_DL(S: np.ndarray, q: int):
    out_idx, in_idx = np.flatnonzero(~S), np.flatnonzero(S)
    Mo, Mi = M[:, out_idx], M[:, in_idx]
    dirs, deltas = [], []
    for name, hr in HR.items():
        for sign, tag in ((1.0, "+"), (-1.0, "-")):
            v = sign * hr
            ib = np.argpartition(-v[out_idx], q)[:q]
            ob = np.argpartition(v[in_idx], q)[:q]
            deltas.append((Mo[:, ib].sum(axis=1) - Mi[:, ob].sum(axis=1)) / K)
            dirs.append(f"{name}{tag}")
    return dirs, np.array(deltas)


def reductions(DL: np.ndarray, res: np.ndarray, cap=4.0):
    num = DL @ res
    den = (DL ** 2).sum(axis=1) + 1e-12
    a = np.clip(num / den, 0, cap)
    return (2 * a * num - a ** 2 * den) / (res ** 2).sum(), a


for label, wpath in BASES:
    w = np.load(wpath)
    s = Tz[:, :15] @ w.astype(np.float32)
    idx = np.argpartition(-s, K)[:K]
    S = np.zeros(len(s), bool)
    S[idx] = True
    res = obs_v - M[:, idx].sum(axis=1) / K
    dirs, DL = build_DL(S, Q)
    red, alpha = reductions(DL, res)
    null = []
    for _ in range(200):
        rp = RNG.permutation(res)
        r2, _ = reductions(DL, rp)
        null.append(r2.max() * (rp ** 2).sum() / (res ** 2).sum())  # same scale
    n95 = float(np.percentile(null, 95))
    top = np.argsort(-red)[:8]
    print(f"\n=== base {label}: res RMSE {np.sqrt((res**2).mean()):.4f}, null95 {n95:.1%} ===")
    for b in top:
        mark = " <<<" if red[b] > n95 else ""
        print(f"  {dirs[b]:18} {red[b]:6.1%}  (~{int(alpha[b]*Q):,} members){mark}")
    for probe in ("f21+", "cluster_blend+", "f19+"):
        b = dirs.index(probe)
        print(f"  [{probe:15}] rank {int((red > red[b]).sum())+1:>2}  {red[b]:6.1%}")
    if label == "current-27":
        cur = (dirs, DL, res, red)

# jackknife on the current era
dirs, DL, res, red_full = cur
print("\n=== jackknife (drop each reading, current era) ===")
ranks_f21, ranks_bl = [], []
for j in range(27):
    m = np.ones(27, bool)
    m[j] = False
    red, _ = reductions(DL[:, m], res[m])
    for probe, acc in (("f21+", ranks_f21), ("cluster_blend+", ranks_bl)):
        b = dirs.index(probe)
        acc.append(int((red > red[b]).sum()) + 1)
    if keys[j] in ("v21", "v6", "v1", "v36"):
        top3 = np.argsort(-red)[:3]
        print(f"  drop {keys[j]:>5}: top3 = {[dirs[b] for b in top3]}, "
              f"f21+ rank {ranks_f21[-1]}, blend rank {ranks_bl[-1]}")
print(f"  f21+ rank: median {int(np.median(ranks_f21))}, worst {max(ranks_f21)}; "
      f"top-3 in {sum(r <= 3 for r in ranks_f21)}/27 jackknives")
print(f"  blend rank: median {int(np.median(ranks_bl))}, worst {max(ranks_bl)}; "
      f"top-3 in {sum(r <= 3 for r in ranks_bl)}/27")

print("\n=== Q sensitivity, current era ===")
s = Tz[:, :15] @ np.load(BASES[0][1]).astype(np.float32)
idx = np.argpartition(-s, K)[:K]
S = np.zeros(len(s), bool)
S[idx] = True
for q in (1000, 2000, 4000):
    dd, DLq = build_DL(S, q)
    red, alpha = reductions(DLq, res)
    for probe in ("f21+", "cluster_blend+"):
        b = dd.index(probe)
        print(f"  Q={q}: {probe:15} rank {int((red > red[b]).sum())+1:>2} "
              f"{red[b]:6.1%} (~{int(alpha[b]*q):,} members)")
