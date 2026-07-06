"""Build data/scores_v43.csv — v43 'pu-max swing' (the highest-ceiling candidate, BENCH-first).

Rationale: every measured-safe gain is already packaged (v42, +0.0003 box). Higher requires
trusting the one signal that retrodicts all 6 non-f3 measured swap outcomes — pu_hgb, the
PU core-resemblance classifier — at a scale far beyond its graded range. This is a priced
swing, not a measured update: SIGN validated, magnitude extrapolated.

Design: base = v37L's set (best measured). Swap N = 2,500:
  IN  = top pu_hgb outsiders (f3 = 0, f11 <= 0.10, margin tie-break)
  OUT = bottom pu_hgb non-whale incumbents (vote, then margin tie-breaks)
Pre-registered: realized = 0.919143 + net * 0.02500, box [0.8941, 0.9441].
Deployment rule: BENCH (DUMMY-2) first; promote to primary via capped-delta only if the
read lands >= ~0.921.

Run: .venv/bin/python scratchpad/build_v43.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
N = 2_500
V37L_EXACT = 0.919143
SHIFT = 0.5403023059          # cos(1) — unique global shift
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
PRIORS = ["v29", "v34", "v35", "v36", "v37L", "v38", "v39", "v40", "v41", "v42"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
Kc = post.shape[0]
pu = np.load(ROOT / "scratchpad" / "tiebreak_signals.npz")["pu_hgb"].astype(np.float64)

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
f21 = df["f21"].fillna(0).to_numpy()
f4 = df["f4"].fillna(0).to_numpy()
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()

sL = pd.read_csv(ROOT / "data" / "scores_v37L.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(sL), bool)
base_mask[np.argpartition(-sL, TOPK)[:TOPK]] = True

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
mr = pd.Series(margin).rank(pct=True).to_numpy()
tb = margin / margin.std()

key_in = pu + 1e-6 * mr
whale = M.all(axis=0)
in_pool = np.flatnonzero(~base_mask & (f3 == 0) & (f11 <= 0.10))
in_pool = in_pool[np.argsort(-key_in[in_pool])][:N]
out_pool = np.flatnonzero(base_mask & ~whale)
out_pool = out_pool[np.lexsort((mr[out_pool], vote[out_pool], pu[out_pool]))][:N]

print(f"IN : pu med {np.median(pu[in_pool]):.3f}  vote med {np.median(vote[in_pool]):.0f}/{Kc}  "
      f"f1 med {np.median(f1[in_pool]):,.0f}  catsum med {np.median(cat[in_pool]):,.0f}  "
      f"f11 med {np.median(f11[in_pool]):.4f}  f21 med {np.median(f21[in_pool]):,.0f}  "
      f"f4 med {np.median(f4[in_pool]):,.0f}")
print(f"OUT: pu med {np.median(pu[out_pool]):.3f}  vote med {np.median(vote[out_pool]):.0f}/{Kc}  "
      f"f1 med {np.median(f1[out_pool]):,.0f}  catsum med {np.median(cat[out_pool]):,.0f}  "
      f"f11 med {np.median(f11[out_pool]):.4f}")
worse = int((pu[in_pool].min() < pu[out_pool]).sum())
print(f"pu-consistency: min IN pu {pu[in_pool].min():.3f} vs max OUT pu {pu[out_pool].max():.3f} "
      f"(OUT members above min-IN: {worse})")

target = base_mask.copy()
target[out_pool] = False
target[in_pool] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

base_new = vote + 1e-3 * tb
assert 1e-3 * np.abs(tb).max() < 0.5
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
      f"corr(id) {r:+.2e}  set-diff vs v37L {int((top ^ base_mask).sum())//2}/{N}  "
      f"overlap vs v37L {(top & base_mask).sum()/TOPK:.4f}")
print(f"E[LB | 28-posterior] {np.mean(lo):.3f} (family-blind to pu by construction — for the record only)")
print(f"PRE-REGISTERED: realized = {V37L_EXACT} + net*{N/1e5:.5f}, "
      f"box [{V37L_EXACT - N/1e5:.4f}, {V37L_EXACT + N/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v43.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
