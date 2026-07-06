"""Residual-displacement fitter — solve for WHICH member-swap direction cancels the
family's 27 reading residuals.

The 15-term fit leaves res_j = actual_j - implied_j (RMSE 0.0037 >> sampling sigma 0.001,
A42). If the truth's top set differs from the fitted set by a displacement along some
direction h (swap the best-q outsiders by h for the worst-q insiders by h), the readings
change by a computable sensitivity vector Delta_h in R^27. Greedy-OMP the residual onto a
~90-direction dictionary (features, transforms, shares, interactions, regime flags, both
signs), with a permutation null to price overfitting 27 noisy points on 90 candidates.

Cheap (~seconds). Complements the sieve: the sieve asks "which generator?", this asks
"which displacement?" — the answer seeds probe design even when no generator threads.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
K = 100_000
Q = 2_000
RNG = np.random.default_rng(7)

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

w15 = np.load(ROOT / "scratchpad" / "tri2_core_w.npy")
s15 = Tz[:, :15] @ w15.astype(np.float32)
order = np.argsort(-s15)
S = np.zeros(len(s15), bool)
S[order[:K]] = True
res = obs_v - M[:, order[:K]].sum(axis=1) / K
print(f"base = core15 fit set; residual RMSE {np.sqrt((res**2).mean()):.4f}, "
      f"|res|max {np.abs(res).max():.4f}")

w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = [names.index(n) for n in ("z1", "z7", "z9", "z10", "exl", "f3neg")]
margin = (Tz[:, SIX] @ w6.astype(np.float32)).astype(np.float64)
margin_r = pd.Series(margin).rank(pct=True).to_numpy()

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), z["ids"])

SPEND = ["f6", "f7", "f8", "f9", "f10"]
g = {c: df[c].fillna(0).to_numpy(np.float64) for c in
     [f"f{i}" for i in range(1, 24)]}
catsum = sum(g[c] for c in SPEND)

D: dict[str, np.ndarray] = {f"f{i}": g[f"f{i}"] for i in range(1, 24)}
D["miss_rew"] = df["f4"].isna().to_numpy(float)
D["miss_line"] = df["f17"].isna().to_numpy(float)
D["miss_nbd"] = df["f6"].isna().to_numpy(float)
D["sqrt_f1"] = np.sqrt(np.clip(g["f1"], 0, None))
D["log_f1"] = np.log1p(np.clip(g["f1"], 0, None))
D["sqrt_cat"] = np.sqrt(np.clip(catsum, 0, None))
D["log_cat"] = np.log1p(np.clip(catsum, 0, None))
for c in SPEND:
    D[f"share_{c}"] = g[c] / (catsum + 1.0)
D["exl"] = g["f11"] * g["f1"]
D["f11cat"] = g["f11"] * catsum
D["dualish"] = pd.Series(catsum).rank(pct=True).to_numpy() * (g["f1"] > 0)
D["redeem_rate"] = g["f21"] / (g["f4"] + 1.0)
D["ben"] = 50 * g["f13"] + g["f14"] + 15 * g["f15"] + g["f16"]
D["ent_credit_util"] = g["f16"] / 64.403398
D["util"] = np.where(g["f17"] > 0, g["f1"] / np.maximum(g["f17"], 1.0), 0.0)
D["supp_blend"] = g["f19"] + 0.5 * g["f20"]
D["engage"] = (pd.Series(g["f12"]).rank(pct=True) + pd.Series(g["f22"]).rank(pct=True)).to_numpy()

# sensitivity vectors: swap top-Q outsiders by h for bottom-Q insiders by h
out_idx = np.flatnonzero(~S)
in_idx = np.flatnonzero(S)
Mo = M[:, out_idx]
Mi = M[:, in_idx]
dirs, deltas = [], []
for name, h in D.items():
    hr = pd.Series(h).rank(pct=True).to_numpy() + 1e-6 * margin_r   # margin tie-break
    for sign, tag in ((1.0, "+"), (-1.0, "-")):
        v = sign * hr
        ib = np.argpartition(-v[out_idx], Q)[:Q]                     # best outsiders by h
        ob = np.argpartition(v[in_idx], Q)[:Q]                       # worst insiders by h
        delta = (Mo[:, ib].sum(axis=1) - Mi[:, ob].sum(axis=1)) / K
        dirs.append(f"{name}{tag}")
        deltas.append(delta)
DL = np.array(deltas)                                                # (n_dirs, 27)
print(f"{len(dirs)} directions, Q={Q}")


def omp(target, DLm, max_terms=3, cap_alpha=4.0):
    r = target.copy()
    picks = []
    for _ in range(max_terms):
        num = DLm @ r
        den = (DLm ** 2).sum(axis=1) + 1e-12
        alpha = np.clip(num / den, 0, cap_alpha)
        red = 2 * alpha * num - alpha ** 2 * den                     # SS reduction per dir
        b = int(np.argmax(red))
        if red[b] <= 0:
            break
        picks.append((b, float(alpha[b]), float(red[b])))
        r = r - alpha[b] * DLm[b]
    return picks, r


ss0 = float((res ** 2).sum())
picks, r_final = omp(res, DL)
print(f"\nresidual SS {ss0:.2e} -> {float((r_final**2).sum()):.2e}")
for b, a, red in picks:
    print(f"  {dirs[b]:20} alpha {a:.2f} (~{int(a*Q):,} members)  SS-reduction {red/ss0:.1%}")

# permutation null: same dictionary, residual entries shuffled (200x), 1-term best reduction
null = []
for _ in range(200):
    rp = RNG.permutation(res)
    num = DL @ rp
    den = (DL ** 2).sum(axis=1) + 1e-12
    alpha = np.clip(num / den, 0, 4.0)
    null.append(float((2 * alpha * num - alpha ** 2 * den).max() / (rp ** 2).sum()))
null = np.array(null)
first_red = picks[0][2] / ss0 if picks else 0.0
print(f"\n1-term SS-reduction: observed {first_red:.1%} vs permutation null "
      f"median {np.median(null):.1%} / 95th {np.percentile(null, 95):.1%}"
      f" -> {'SIGNAL' if first_red > np.percentile(null, 95) else 'not above noise'}")

# stability of the top direction across Q
if picks:
    b0 = picks[0][0]
    base_name = dirs[b0][:-1]
    sign = 1.0 if dirs[b0].endswith("+") else -1.0
    hr = pd.Series(D[base_name]).rank(pct=True).to_numpy() + 1e-6 * margin_r
    v = sign * hr
    for q in (1000, 4000):
        ib = np.argpartition(-v[out_idx], q)[:q]
        ob = np.argpartition(v[in_idx], q)[:q]
        d = (Mo[:, ib].sum(axis=1) - Mi[:, ob].sum(axis=1)) / K
        a = float(np.clip(d @ res / ((d ** 2).sum() + 1e-12), 0, 4))
        print(f"  top dir at Q={q}: SS-reduction {(2*a*(d@res) - a*a*(d**2).sum())/ss0:.1%}")

print("\ntop 12 single directions by SS-reduction:")
num = DL @ res
den = (DL ** 2).sum(axis=1) + 1e-12
alpha = np.clip(num / den, 0, 4.0)
red = (2 * alpha * num - alpha ** 2 * den) / ss0
for b in np.argsort(-red)[:12]:
    print(f"  {dirs[b]:20} {red[b]:6.1%}  alpha {alpha[b]:.2f} (~{int(alpha[b]*Q):,} members)")
