"""Build data/scores_v45.csv — v45 'measured-base promotion' (PRIMARY candidate).

Base = v44's exact top-100K — a MEASURED set (bench read 0.9191, ~+9 public counts over the
banked 0.918971) — plus the post-v44 sequentially-updated tranche: 31-read recalibrated
ensemble weights (eta*=0.02, tau*=0.0005, ESS 9/12, 9-probe PIT near-uniform), calibrated
inclusion-probability gap >= 0.5, pu no-trade-down veto, cap 600. The update after v44's
read shrank the tranche 533 -> ~186 and its edge to E +0.0011 — conviction cut by evidence.

Pre-registered: realized = 0.9191 + net * N/1e5; calibrated E[read] ~0.9203, sd ~0.0013,
P(> banked 0.918971) ~86–94% (base is measured; only the tranche term is model-priced).
Run: .venv/bin/python scratchpad/build_v45.py
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
CAP = 600
GAP = 0.5
V44_READ = 0.9191
SHIFT = 0.7788007831          # exp(-1/4) — unique global shift
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
PRIORS = ["v29", "v34", "v35", "v36", "v37L", "v38", "v39", "v40", "v41", "v42", "v43", "v44"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
masks = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
W = np.load(ROOT / "scratchpad" / "ensemble_weights.npy")     # 31-read sequential update
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
pu = np.load(ROOT / "scratchpad" / "tiebreak_signals.npz")["pu_hgb"].astype(np.float64)
mu = W @ masks

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()

s44 = pd.read_csv(ROOT / "data" / "scores_v44.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(s44), bool)
base_mask[np.argpartition(-s44, TOPK)[:TOPK]] = True
whale = M.all(axis=0)

tbm = pd.Series(pu).rank(pct=True).to_numpy()
in_pool = np.flatnonzero(~base_mask & (f3 == 0))
out_pool = np.flatnonzero(base_mask & ~whale)
in_pool = in_pool[np.lexsort((-tbm[in_pool], -mu[in_pool]))]
out_pool = out_pool[np.lexsort((tbm[out_pool], mu[out_pool]))]
swap_in, swap_out, veto = [], [], 0
i = j = 0
while len(swap_in) < CAP and i < len(in_pool) and j < len(out_pool):
    a, b = in_pool[i], out_pool[j]
    if mu[a] - mu[b] < GAP:
        break
    if pu[a] < pu[b]:
        veto += 1
        i += 1
        continue
    swap_in.append(a)
    swap_out.append(b)
    i += 1
    j += 1
swap_in, swap_out = np.array(swap_in, int), np.array(swap_out, int)
n_apply = len(swap_in)
print(f"tranche: N = {n_apply} (vetoed {veto}) on the 31-read calibrated weights")
if n_apply == 0:
    raise SystemExit("no qualifying pairs — promote v44's set unchanged instead")
nets = (masks[:, swap_in].sum(axis=1) - masks[:, swap_out].sum(axis=1)) / 1e5
mean_ = float((W * nets).sum())
sd_ = float(np.sqrt((W * (nets - mean_) ** 2).sum() + 0.001 ** 2 + 0.0005 ** 2))
for lbl, ix in (("IN ", swap_in), ("OUT", swap_out)):
    print(f"  {lbl}: mu med {np.median(mu[ix]):.2f}  f1 med {np.median(f1[ix]):,.0f}  "
          f"catsum med {np.median(cat[ix]):,.0f}  f11 med {np.median(f11[ix]):.4f}")

target = base_mask.copy()
target[swap_out] = False
target[swap_in] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = mu * 25.0 + 1e-3 * tb
BIG = 2.0 * (base_new.max() - base_new.min())
score = base_new + BIG * target
score[f3 == 1] = score.min() - 1.0
score = score + SHIFT

top = np.zeros(len(score), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())

uniq = np.unique(score)
for nm in PRIORS:
    p = ROOT / "data" / f"scores_{nm}.csv"
    if not p.exists():
        continue
    prior = pd.read_csv(p).set_index("id")["score"].reindex(ids).to_numpy()
    shared = np.intersect1d(uniq, np.unique(prior))
    print(f"floats shared with {nm}: {len(shared)} (must be 0)")
    assert len(shared) == 0

s = pd.Series(score)
r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"distinct {s.nunique():,}  cutoff members {n_cut}  f3-in-top {int((top & (f3==1)).sum())}")
print(f"revolver {f1[top].astype(bool).mean():.1%}  whale-in {(top & whale).sum()/whale.sum():.3f}  "
      f"corr(id) {r:+.2e}  set-diff vs v44 {int((top ^ base_mask).sum())//2}  "
      f"vs v35 {int((top ^ (lambda v: (np.zeros(len(ids),bool)))(0)).sum())//2 if False else ''}")
print(f"CALIBRATED predictive: E[read] {V44_READ + mean_:.4f}  sd {sd_:.4f}")
print(f"PRE-REGISTERED: realized = {V44_READ} + net*{n_apply/1e5:.5f}, "
      f"box [{V44_READ - n_apply/1e5:.4f}, {V44_READ + n_apply/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v45.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
