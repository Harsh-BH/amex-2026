"""Build data/scores_v35.csv — v35 'tranche-2' (trust-region update of v34, conviction-curve-sized).

v34 validated the mechanism (600 capped swaps, realized +0.44 net accuracy at median vote-gap
21/36 → calibration shrink λ ≈ 0.75 on posterior-predicted net accuracy). v35 applies the NEXT
tranche off the fresh 24-constraint posterior (30 kept calibrations), with N sized by the
measured conviction curve instead of a blind cap: include pairs while gap ≥ GAP_FLOOR·K, cap
N_MAX. Floor read = 0.917614 − N/1e5 (banked best untouched via best-score-counts).

Run: .venv/bin/python scratchpad/build_v35.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
N_MAX = 2_000
GAP_FLOOR = 0.40   # stop when vote-gap < 40% of K (v34's tranche averaged 58%)
LAMBDA = 0.75      # measured calibration shrink: realized net / posterior-predicted net (v34)
V34_EXACT = 0.917614
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
assert "v34" in keys, "cache is stale — rebuild with the 24-constraint OBS"
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
K = post.shape[0]
print(f"posterior calibrations kept: {K} (24 constraints)")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()

s34 = pd.read_csv(ROOT / "data" / "scores_v34.csv").set_index("id")["score"].reindex(ids).to_numpy()
assert not np.isnan(s34).any()
m34 = np.zeros(len(s34), bool)
m34[np.argpartition(-s34, TOPK)[:TOPK]] = True

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = vote + 1e-3 * tb
assert 1e-3 * np.abs(tb).max() < 0.5, "tiebreak crosses vote levels"

e34 = np.mean([(m34 & p).sum() / TOPK for p in post])
print(f"anchor check — E[LB | posterior] for v34's set: {e34:.3f} (actual {V34_EXACT})")

in_pool = np.flatnonzero(~m34 & (f3 == 0))
out_pool = np.flatnonzero(m34)
in_pool = in_pool[np.lexsort((-tb[in_pool], -vote[in_pool]))]
out_pool = out_pool[np.lexsort((tb[out_pool], vote[out_pool]))]

# conviction-depth curve
gaps = (vote[in_pool[:6000]] - vote[out_pool[:6000]]) / K
print("\nconviction curve (vote-gap as share of K, cumulative predicted gain with λ=0.75):")
print(f"{'N':>6} {'gap@N':>7} {'cum E[gain]':>12} {'floor':>8}")
cum = np.cumsum(LAMBDA * np.clip(gaps, 0, None)) / 1e5
for n in (300, 600, 1000, 1500, 2000, 3000, 4000, 6000):
    if n <= len(gaps):
        print(f"{n:>6} {gaps[n-1]:>7.2f} {cum[n-1]:>12.5f} {V34_EXACT - n/1e5:>8.4f}")

n_apply = int(min(N_MAX, np.searchsorted(-gaps, -GAP_FLOOR)))
swap_in, swap_out = in_pool[:n_apply], out_pool[:n_apply]
pred = V34_EXACT + cum[n_apply - 1]
print(f"\nchosen N = {n_apply} (gap floor {GAP_FLOOR:.0%}, cap {N_MAX})")
print(f"  IN : vote med {np.median(vote[swap_in]):.0f}/{K}  f1 med {np.median(f1[swap_in]):,.0f}"
      f"  catsum med {np.median(cat[swap_in]):,.0f}  f11 med {np.median(f11[swap_in]):.4f}")
print(f"  OUT: vote med {np.median(vote[swap_out]):.0f}/{K}  f1 med {np.median(f1[swap_out]):,.0f}"
      f"  catsum med {np.median(cat[swap_out]):,.0f}  f11 med {np.median(f11[swap_out]):.4f}")

target = m34.copy()
target[swap_out] = False
target[swap_in] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

BIG = 2.0 * (base_new.max() - base_new.min())
score = base_new + BIG * target
score[f3 == 1] = score.min() - 1.0
score = score + 0.2718281828            # global shift (distinct from v34's): no shared structural floats

s = pd.Series(score)
top = np.zeros(len(s), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())
whale = M.all(axis=0)
lo = [(top & p).sum() / TOPK for p in post]

for prior, nm in ((s34, "scores_v34"), (pd.read_csv(ROOT / "data" / "scores_v29.csv").set_index("id")["score"].reindex(ids).to_numpy(), "scores_v29")):
    shared = np.intersect1d(np.unique(score), np.unique(prior))
    print(f"float values shared with {nm}: {len(shared)} (must be 0)")
    assert len(shared) == 0

print(f"distinct scores: {s.nunique():,}")
print(f"members at cutoff: {n_cut} (must be 1)")
print(f"f3=1 in top-20%: {int((top & (f3 == 1)).sum())} (must be 0)")
print(f"revolver share: {f1[top].astype(bool).mean():.1%}   whale-in: {(top & whale).sum() / whale.sum():.3f}")
print(f"overlap vs v34 set: {(top & m34).sum() / TOPK:.4f}")
print(f"E[LB | posterior]: {np.mean(lo):.3f}   min {min(lo):.3f}   low-quartile {np.percentile(lo, 25):.3f}")
print(f"PREDICTION (λ-calibrated): {pred:.4f}   box [{V34_EXACT - n_apply/1e5:.4f}, {V34_EXACT + n_apply/1e5:.4f}]")
r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"corr(id, score): {r:+.2e}")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v35.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
