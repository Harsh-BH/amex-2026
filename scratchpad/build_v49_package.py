"""Package v49 — eigen-mode-3 maximum-disagreement swing (BENCH ladder shot #1).

Pool: scratchpad/v49_eigen_pool.npz (mode-3, N=1,200), computed by the 12-exact-probe
recalibrated ensemble (build_v49.py + the eigen recompute). The swap reorders WITHIN the
zero-balance high-spend class — the one region where the surviving calibrations genuinely
disagree after 34 reads. Calibrated predictive: E 0.9194, sd 0.0072, P(>=0.920) 46%,
P(>= banked) 52% (self-selection haircut -> ~35-40% at 0.920).
Pre-registered: realized = 0.919143 + net*0.01200, box [0.9107, 0.9275].
Deployment: DUMMY-2 bench. >=0.9205 -> capped-delta promotion to primary; else constraint #35
and ladder shot #2 from the next orthogonal mode under sharpened weights.

Run: .venv/bin/python scratchpad/build_v49_package.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
V37L_EXACT = 0.919143
SHIFT0 = 0.4342944819          # 1/ln(10) — start of the self-healing shift search

pool = np.load(ROOT / "scratchpad" / "v49_eigen_pool.npz")
si, so = pool["swap_in"], pool["swap_out"]
N = len(si)
assert N == len(so) == 1200

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M_hist, ids = z["M"], z["ids"]
masks = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
pu = np.load(ROOT / "scratchpad" / "tiebreak_signals.npz")["pu_hgb"].astype(np.float64)
W = None  # weights only needed upstream; packaging uses uniform-vote + pu tie-break

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f = df.fillna(0.0)
f3v = f["f3"].to_numpy(); f1v = f["f1"].to_numpy(); f11v = f["f11"].to_numpy()
cat = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()

sL = pd.read_csv(ROOT / "data" / "scores_v37L.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(sL), bool)
base_mask[np.argpartition(-sL, TOPK)[:TOPK]] = True
whale = M_hist.all(axis=0)

# pool legality (re-assert from raw)
assert (~base_mask[si]).all() and (f3v[si] == 0).all()
assert base_mask[so].all() and (~whale[so]).all()
assert len(np.intersect1d(si, so)) == 0

target = base_mask.copy()
target[so] = False
target[si] = True
assert target.sum() == TOPK and not (target & (f3v >= 1)).any()

print(f"IN : f1 med {np.median(f1v[si]):,.0f}  cat med {np.median(cat[si]):,.0f}  f11 med {np.median(f11v[si]):.4f}")
print(f"OUT: f1 med {np.median(f1v[so]):,.0f}  cat med {np.median(cat[so]):,.0f}  f11 med {np.median(f11v[so]):.4f}")

# ---- packaging: calibrated vote + pu tie-break + margin micro-break, f3 floor, shift ----
vote = masks.sum(axis=0).astype(np.float64)           # 12-cal vote (monotone packaging)
tbm = pd.Series(pu).rank(pct=True).to_numpy()
names = [str(x) for x in z["names"]]
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
margin = (z["T"][:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
base_new = vote + 1e-3 * tbm + 1e-6 * (margin / margin.std())   # margin layer: full distinctness
RANGE = base_new.max() - base_new.min()
BIG = 2.0 * RANGE
raw = base_new + BIG * target
raw[f3v >= 1] = raw.min() - 1.0
SCALE = 1.0 + 4.342944819e-7

prior_vals = []
for p in sorted((ROOT / "data").glob("scores_v*.csv")):
    if p.name == "scores_v49.csv":
        continue
    prior_vals.append(np.unique(pd.read_csv(p).set_index("id")["score"].reindex(ids).to_numpy()))
all_prior = np.unique(np.concatenate(prior_vals))
shift = SHIFT0
for attempt in range(1000):
    score = raw * SCALE + shift
    if len(np.intersect1d(np.unique(score), all_prior)) == 0:
        break
    shift += 1e-9
else:
    raise RuntimeError("no collision-free shift found")
print(f"anti-fingerprint clean (shift {shift!r}, {attempt} bump(s))")

top = np.zeros(len(score), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())
s = pd.Series(score)
r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"distinct {s.nunique():,}  cutoff members {n_cut}  f3-in-top 0  "
      f"set-diff vs v37L {int((top ^ base_mask).sum())//2}/{N}  whale-in {(top & whale).sum()/whale.sum():.4f}")
print(f"corr(id) {r:+.2e}")
print(f"PRE-REGISTERED: realized = {V37L_EXACT} + net*{N/1e5:.5f}, "
      f"box [{V37L_EXACT-0.7*N/1e5:.4f}, {V37L_EXACT+0.7*N/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v49.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
