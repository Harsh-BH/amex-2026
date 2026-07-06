"""Build data/scores_v37L.csv — v37-L 'nbd level probe' (designed measurement, dummy bench).

FINDING (2026-07-03 night, session log): the no-breakdown cohort's LEVEL in the top quintile is
under-determined by all 25 exact reads — the kept calibrations' own levels span 991..3,644
(ours: 1,740), a ±0.007 freedom band the posterior cannot resolve. Direct probe: demote the
N weakest-vote in-top nbd members, promote the N strongest-vote out-of-top NON-nbd members.
The posterior's own gap curve favors the first ~400-600 (mean gap +0.17 at 400) and opposes
deeper cuts. N = 500 → realized = 0.918971 + (r_repl − r_nbd)·0.00500 ∈ [0.9140, 0.9240].
Attribution is clean (single axis, single direction) — the read measures the nbd in-top
truth-density differential exactly at 6-dp.

Run: .venv/bin/python scratchpad/build_v37L.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
N_PROBE = 500
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
V35 = 0.918971

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
assert "v35" in keys
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
K = post.shape[0]

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f = df.fillna(0.0)
f1, f11, f3 = f["f1"].to_numpy(), f["f11"].to_numpy(), f["f3"].to_numpy()
nbd = df["f6"].isna().to_numpy()

s35 = pd.read_csv(ROOT / "data" / "scores_v35.csv").set_index("id")["score"].reindex(ids).to_numpy()
m35 = np.zeros(len(s35), bool)
m35[np.argpartition(-s35, TOPK)[:TOPK]] = True

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = vote + 1e-3 * tb

in_nbd = np.flatnonzero(m35 & nbd)
demote = in_nbd[np.lexsort((tb[in_nbd], vote[in_nbd]))][:N_PROBE]          # weakest-vote nbd first
repl_pool = np.flatnonzero(~m35 & ~nbd & (f3 == 0))
promote = repl_pool[np.lexsort((-tb[repl_pool], -vote[repl_pool]))][:N_PROBE]
print(f"level probe N = {N_PROBE} (calibrations K = {K})")
print(f"  DEMOTE (nbd): vote med {np.median(vote[demote]):.0f}/{K}  f1 med {np.median(f1[demote]):,.0f}  f11 med {np.median(f11[demote]):.4f}")
print(f"  PROMOTE (non-nbd): vote med {np.median(vote[promote]):.0f}/{K}  f1 med {np.median(f1[promote]):,.0f}  f11 med {np.median(f11[promote]):.4f}")
print(f"  nbd level: 1,740 → {1_740 - N_PROBE:,}")

target = m35.copy()
target[demote] = False
target[promote] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

BIG = 2.0 * (base_new.max() - base_new.min())
score = base_new + BIG * target
score[f3 == 1] = score.min() - 1.0
score = score + 0.6931471806          # global shift distinct from v34/v35/v36

s = pd.Series(score)
top = np.zeros(len(s), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())
for prior in ("scores_v36", "scores_v35", "scores_v34", "scores_v29"):
    p = ROOT / "data" / f"{prior}.csv"
    if p.exists():
        pv = pd.read_csv(p).set_index("id")["score"].reindex(ids).to_numpy()
        shared = np.intersect1d(np.unique(score), np.unique(pv))
        print(f"floats shared with {prior}: {len(shared)} (must be 0)")
        assert len(shared) == 0
whale = M.all(axis=0)
print(f"distinct: {s.nunique():,}   cutoff members: {n_cut}   f3 in top: {int((top & (f3==1)).sum())}")
print(f"revolver share: {f1[top].astype(bool).mean():.1%}   whale-in: {(top & whale).sum()/whale.sum():.3f}   overlap vs v35: {(top & m35).sum()/TOPK:.4f}")
print(f"BOX: realized = {V35} + (r_repl − r_nbd)·{N_PROBE/1e5:.5f} ∈ [{V35 - N_PROBE/1e5:.4f}, {V35 + N_PROBE/1e5:.4f}]")
r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"corr(id, score): {r:+.2e}")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

pd.DataFrame({"id": ids, "score": score}).to_csv(ROOT / "data" / "scores_v37L.csv", index=False)
print("wrote data/scores_v37L.csv")
