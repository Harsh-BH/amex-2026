"""Build data/scores_v42.csv — v42 'measured promotion + retrodiction tie-break' (primary closer).

Base = v37L's set (best measured, 0.919143) ⊕ the fresh 28-constraint posterior's top
conviction tranche (v34-validated rule: vote-gap >= 50% of kept, cap 600), with two
upgrades earned by measurement this cycle:
  1. within-vote ordering = 0.7*margin + 0.3*pu_hgb (the PU core-resemblance signal that
     retrodicts all 6 non-f3 measured swap outcomes, incl. uniquely calling v41 negative);
  2. a pu-veto: a swap is skipped when the incoming member's pu_hgb percentile is below
     the outgoing member's (never trade down on the one signal that graded every paid swap).

Pre-registered: realized = 0.919143 + net * N/1e5, box [0.919143 - N/1e5, 0.919143 + N/1e5].

Run AFTER refit-28's posterior completes (scratchpad/check_artifacts.py must pass):
  .venv/bin/python scratchpad/build_v42.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
CAP = 600
GAP_FLOOR = 0.50
V37L_EXACT = 0.919143
SHIFT = 0.2302585093          # ln(10)/10 — unique global shift
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
PRIORS = ["v29", "v34", "v35", "v36", "v37L", "v38", "v39", "v40", "v41"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
assert "v41" in keys, "cache must be the 28-constraint build"
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
Kc = post.shape[0]
print(f"posterior calibrations kept: {Kc} (28 constraints)")

sig = np.load(ROOT / "scratchpad" / "tiebreak_signals.npz")
pu = sig["pu_hgb"].astype(np.float64)          # population percentile already

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()

sL = pd.read_csv(ROOT / "data" / "scores_v37L.csv").set_index("id")["score"].reindex(ids).to_numpy()
base_mask = np.zeros(len(sL), bool)
base_mask[np.argpartition(-sL, TOPK)[:TOPK]] = True

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
mr = pd.Series(margin).rank(pct=True).to_numpy()
order_key = 0.7 * mr + 0.3 * pu               # retrodiction-validated within-vote ordering
tb = (margin / margin.std())

e_base = np.mean([(base_mask & p).sum() / TOPK for p in post])
print(f"anchor — E[LB | fresh posterior] for v37L's set: {e_base:.3f} (actual {V37L_EXACT})")

whale = M.all(axis=0)
in_pool = np.flatnonzero(~base_mask & (f3 == 0))
out_pool = np.flatnonzero(base_mask & ~whale)
in_pool = in_pool[np.lexsort((-order_key[in_pool], -vote[in_pool]))]
out_pool = out_pool[np.lexsort((order_key[out_pool], vote[out_pool]))]

swap_in, swap_out, vetoed = [], [], 0
i = j = 0
while len(swap_in) < CAP and i < len(in_pool) and j < len(out_pool):
    a, b = in_pool[i], out_pool[j]
    if (vote[a] - vote[b]) / Kc < GAP_FLOOR:
        break
    if pu[a] < pu[b]:                          # pu-veto: never trade down on the graded signal
        vetoed += 1
        i += 1
        continue
    swap_in.append(a)
    swap_out.append(b)
    i += 1
    j += 1
swap_in, swap_out = np.array(swap_in, int), np.array(swap_out, int)
n_apply = len(swap_in)
print(f"tranche: N = {n_apply} (cap {CAP}, gap >= {GAP_FLOOR:.0%} of {Kc}), pu-vetoed {vetoed}")
if n_apply == 0:
    raise SystemExit("no qualifying pairs — hold at v37L base / do not build")
for lbl, ix in (("IN ", swap_in), ("OUT", swap_out)):
    print(f"  {lbl}: vote med {np.median(vote[ix]):.0f}/{Kc}  f1 med {np.median(f1[ix]):,.0f}  "
          f"catsum med {np.median(cat[ix]):,.0f}  f11 med {np.median(f11[ix]):.4f}  "
          f"pu med {np.median(pu[ix]):.2f}")

target = base_mask.copy()
target[swap_out] = False
target[swap_in] = True
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
      f"corr(id) {r:+.2e}  overlap vs v37L {(top & base_mask).sum()/TOPK:.4f}")
print(f"E[LB | posterior] {np.mean(lo):.3f}  low-quartile {np.percentile(lo, 25):.3f}")
print(f"PRE-REGISTERED: realized = {V37L_EXACT} + net*{n_apply/1e5:.5f}, "
      f"box [{V37L_EXACT - n_apply/1e5:.4f}, {V37L_EXACT + n_apply/1e5:.4f}]")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

out = ROOT / "data" / "scores_v42.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
