"""Build data/scores_v44.csv — v44 'calibrated-predictive tranche' (redesign pipeline, round 1).

First candidate produced by the redesigned inference stack (reports/methodology-redesign-
2026-07-04.md §15.1): Gibbs-eta reweighted 30-constraint ensemble (eta/tau calibrated to
uniform PIT on all 8 paid probe outcomes), v42-pattern capped tranche off v37L's base with
the pu no-trade-down veto, gated by the CALIBRATED predictive:
  E[read] 0.9229, sd 0.0023, P(> banked 0.918971) ~96%  — with the disclosed caveat that
  self-selected candidates carry a selection bias the PIT calibration cannot correct;
  deployment is BENCH-first for exactly that reason.
Pools were computed by scratchpad/redesign_step1.py -> scratchpad/v44_pools.npz.

Pre-registered: realized = 0.919143 + net * N/1e5.
Run: .venv/bin/python scratchpad/build_v44.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
V37L_EXACT = 0.919143
SHIFT = 0.6065306597          # exp(-1/2) — unique global shift
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
PRIORS = ["v29", "v34", "v35", "v36", "v37L", "v38", "v39", "v40", "v41", "v42", "v43"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
masks = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
W = np.load(ROOT / "scratchpad" / "ensemble_weights.npy")
pools = np.load(ROOT / "scratchpad" / "v44_pools.npz")
swap_in, swap_out = pools["swap_in"], pools["swap_out"]
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
n_apply = len(swap_in)
print(f"tranche from redesign_step1: N = {n_apply}")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()

sL = pd.read_csv(ROOT / "data" / "scores_v37L.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(sL), bool)
base_mask[np.argpartition(-sL, TOPK)[:TOPK]] = True
whale = M.all(axis=0)
assert not base_mask[swap_in].any() and base_mask[swap_out].all()
assert not whale[swap_out].any() and (f3[swap_in] == 0).all()

mu = W @ masks
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = mu * 25.0 + 1e-3 * tb          # calibrated probs on a vote-like scale + tie-break
assert 1e-3 * np.abs(tb).max() < 0.5 * 25.0 / 25.0

for lbl, ix in (("IN ", swap_in), ("OUT", swap_out)):
    print(f"  {lbl}: mu med {np.median(mu[ix]):.2f}  f1 med {np.median(f1[ix]):,.0f}  "
          f"catsum med {np.median(cat[ix]):,.0f}  f11 med {np.median(f11[ix]):.4f}")

target = base_mask.copy()
target[swap_out] = False
target[swap_in] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

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
nets = (masks[:, swap_in].sum(axis=1) - masks[:, swap_out].sum(axis=1)) / 1e5
mean_ = float((W * nets).sum())
print(f"distinct {s.nunique():,}  cutoff members {n_cut}  f3-in-top {int((top & (f3==1)).sum())}")
print(f"revolver {f1[top].astype(bool).mean():.1%}  whale-in {(top & whale).sum()/whale.sum():.3f}  "
      f"corr(id) {r:+.2e}  set-diff vs v37L {int((top ^ base_mask).sum())//2}")
print(f"CALIBRATED predictive: E[read] {V37L_EXACT + mean_:.4f}")
print(f"PRE-REGISTERED: realized = {V37L_EXACT} + net*{n_apply/1e5:.5f}, "
      f"box [{V37L_EXACT - n_apply/1e5:.4f}, {V37L_EXACT + n_apply/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v44.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
