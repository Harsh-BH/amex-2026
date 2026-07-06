"""Build data/scores_v39.csv — v39 'redemption-engagement probe' (candidate B1, SWING).

Hypothesis (2026-07-04 red-team, residual-displacement fitter): the hidden truth's top
quintile contains ~1.2-1.4K heavy-REDEEMING members (f21 rewards-points-redeemed flow)
that every in-family calibration excludes (posterior vote median 0/25) — the top residual
direction across all 27 exact readings (21.9% SS-reduction, rank 1 in 25/27 reading
jackknives, above the 200-permutation null; era-recurring as part of the relationship-
breadth cluster). Business reading: redemption activity marks engaged, retained,
multi-product relationships whose forward revenue the pure spend+interest margin misses.

Design: v35's banked set (judged best, 0.918971 exact) with N=1,200 swaps —
  IN : top outsiders by pct-rank(f21, 0-filled), guards f3=0 and f11<=0.10,
       margin tie-break (the fitter's exact construction)
  OUT: weakest (vote, margin) insiders, whale-guarded
Pre-registered: realized = 0.918971 + (r_in - r_out) * 0.01200, box [0.9070, 0.9310].
If displacement real (r_in-r_out ~ +0.35-0.55): 0.923-0.926. If wrong (~ -0.25): ~0.916.
Posterior E[LB] will read LOW by construction (out-of-family swap — same as v36's B).

Run: .venv/bin/python scratchpad/build_v39.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
N = 1_200
V35_EXACT = 0.918971
SHIFT = 0.3010299957          # log10(2) — unique global shift
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
PRIORS = ["v29", "v34", "v35", "v36", "v37L", "v38"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
assert "v36" in keys, "cache stale"
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
Kc = post.shape[0]

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
f21 = df["f21"].fillna(0).to_numpy()
f4 = df["f4"].fillna(0).to_numpy()
f19 = df["f19"].fillna(0).to_numpy()
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()

s35 = pd.read_csv(ROOT / "data" / "scores_v35.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(s35), bool)
base_mask[np.argpartition(-s35, TOPK)[:TOPK]] = True

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
margin_r = pd.Series(margin).rank(pct=True).to_numpy()
h = pd.Series(f21).rank(pct=True).to_numpy() + 1e-6 * margin_r   # the fitter's exact ranking

ok_in = ~base_mask & (f3 == 0) & (f11 <= 0.10)
in_pool = np.flatnonzero(ok_in)
in_pool = in_pool[np.argsort(-h[in_pool])][:N]
whale = M.all(axis=0)                       # never demote a consensus whale (A34 doctrine)
out_pool = np.flatnonzero(base_mask & ~whale)
out_pool = out_pool[np.lexsort((tb[out_pool], vote[out_pool]))][:N]
print(f"IN : f21 med {np.median(f21[in_pool]):,.0f}  f4 med {np.median(f4[in_pool]):,.0f}  "
      f"f1 med {np.median(f1[in_pool]):,.0f}  catsum med {np.median(cat[in_pool]):,.0f}  "
      f"f11 med {np.median(f11[in_pool]):.4f}  f19 med {np.median(f19[in_pool]):.0f}  "
      f"vote med {np.median(vote[in_pool]):.0f}/{Kc}")
print(f"OUT: f21 med {np.median(f21[out_pool]):,.0f}  f1 med {np.median(f1[out_pool]):,.0f}  "
      f"catsum med {np.median(cat[out_pool]):,.0f}  f11 med {np.median(f11[out_pool]):.4f}  "
      f"vote med {np.median(vote[out_pool]):.0f}/{Kc}")

target = base_mask.copy()
target[out_pool] = False
target[in_pool] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

base_new = vote + 1e-3 * tb
BIG = 2.0 * (base_new.max() - base_new.min())
score = base_new + BIG * target
score[f3 == 1] = score.min() - 1.0
score = score + SHIFT

top = np.zeros(len(score), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())
lo = [(top & p).sum() / TOPK for p in post]

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
      f"corr(id) {r:+.2e}  set-diff vs v35 {int((top ^ base_mask).sum())//2}/{N}")
print(f"E[LB | posterior] {np.mean(lo):.3f} (expected LOW — out-of-family by design)")
print(f"PRE-REGISTERED: realized = {V35_EXACT} + (r_in - r_out)*{N/1e5:.5f}, "
      f"box [{V35_EXACT - N/1e5:.4f}, {V35_EXACT + N/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v39.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
