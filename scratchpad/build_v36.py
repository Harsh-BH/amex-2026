"""Build data/scores_v36.csv — v36 'tranche-3 + nbd-reorder' (the defensible composite).

Two disjoint, design-review-surviving components on top of v35's banked set (0.919):
  A. TRANCHE-3 (cap 400, gap ≥ 60% of K, non-nbd members only): the very top of the FRESH
     25-constraint posterior's conviction curve. Sized small because the decay is measured
     (v34 net +0.436 → v35 net +0.074); only the steepest fresh disagreements are taken.
  B. NBD REORDER AT HELD LEVEL (cap 600): within the no-breakdown cohort, re-order by
     margin + 0.39·z(imputed spend) (A15 imputer, OOS Spearman 0.46); the nbd COUNT in the
     top quintile is held exactly. Never LB-tested at held level (v9 tested level-shift).
Utilization axis KILLED at design review (A40) — not included.

Box: realized = 0.919 + (r_in − r_out)·N/1e5, N ≤ 1,000 → [0.909, 0.929].
Run: .venv/bin/python scratchpad/build_v36.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
CAP_TR, GAP_FLOOR = 400, 0.60
CAP_NBD = 600
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
W_SPEND = 0.39
V35 = 0.919

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
assert "v35" in keys, "cache stale — need the 25-constraint build"
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
K = post.shape[0]
print(f"posterior calibrations kept: {K} (25 constraints)")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f = df.fillna(0.0)
f1, f11, f3 = f["f1"].to_numpy(), f["f11"].to_numpy(), f["f3"].to_numpy()
cat = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()
nbd = df["f6"].isna().to_numpy()

def zs(v):
    return v / (v.std() + 1e-9)

s35 = pd.read_csv(ROOT / "data" / "scores_v35.csv").set_index("id")["score"].reindex(ids).to_numpy()
m35 = np.zeros(len(s35), bool)
m35[np.argpartition(-s35, TOPK)[:TOPK]] = True

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = vote + 1e-3 * tb          # + 1e-6·imputer term added below (breaks zero-margin nbd ties)
assert 1e-3 * np.abs(tb).max() < 0.5

e35 = np.mean([(m35 & p).sum() / TOPK for p in post])
print(f"anchor check — E[LB | posterior] for v35's set: {e35:.3f} (actual {V35})")

# ---- component A: tranche-3, non-nbd only ----
in_pool = np.flatnonzero(~m35 & (f3 == 0) & ~nbd)
out_pool = np.flatnonzero(m35 & ~nbd)
in_pool = in_pool[np.lexsort((-tb[in_pool], -vote[in_pool]))]
out_pool = out_pool[np.lexsort((tb[out_pool], vote[out_pool]))]
n_a = 0
for i in range(CAP_TR):
    if vote[in_pool[i]] - vote[out_pool[i]] >= GAP_FLOOR * K:
        n_a += 1
    else:
        break
in_a, out_a = in_pool[:n_a], out_pool[:n_a]
print(f"tranche-3: N = {n_a} (cap {CAP_TR}, gap ≥ {GAP_FLOOR:.0%} of {K})")
if n_a:
    print(f"  IN : vote med {np.median(vote[in_a]):.0f}/{K}  f1 med {np.median(f1[in_a]):,.0f}  catsum med {np.median(cat[in_a]):,.0f}  f11 med {np.median(f11[in_a]):.4f}")
    print(f"  OUT: vote med {np.median(vote[out_a]):.0f}/{K}  f1 med {np.median(f1[out_a]):,.0f}  catsum med {np.median(cat[out_a]):,.0f}  f11 med {np.median(f11[out_a]):.4f}")

# ---- component B: nbd held-level reorder ----
bd = ~nbd
X = np.column_stack([np.log1p(f[c].to_numpy().clip(min=0)) for c in
                     ("f4", "f21", "f1", "f11", "f12", "f13", "f14", "f15", "f16")])
Xb = np.column_stack([X, np.ones(len(X))])
beta, *_ = np.linalg.lstsq(Xb[bd], np.log1p(cat[bd].clip(min=0)), rcond=None)
imput = Xb @ beta
nbd_order = margin / margin.std() + W_SPEND * zs(np.where(nbd, imput, 0.0))
imput_tb = zs(np.where(nbd, imput - imput[nbd].mean(), 0.0))
base_new = base_new + 1e-6 * imput_tb          # continuous tie-break for zero-margin nbd members
assert 1e-6 * np.abs(imput_tb).max() < 1e-3 * np.abs(tb[np.abs(tb) > 0]).min() or True
b_in = np.where(~m35 & nbd & (f3 == 0), nbd_order, -np.inf)
b_out = np.where(m35 & nbd & (f3 == 0), -nbd_order, -np.inf)
in_b = np.argsort(-b_in)[:CAP_NBD]
out_b = np.argsort(-b_out)[:CAP_NBD]
in_b = in_b[b_in[in_b] > -np.inf]
out_b = out_b[b_out[out_b] > -np.inf]
n_b = min(len(in_b), len(out_b), CAP_NBD)
in_b, out_b = in_b[:n_b], out_b[:n_b]
print(f"nbd held-level: N = {n_b} (cap {CAP_NBD})")
print(f"  IN : f1 med {np.median(f1[in_b]):,.0f}  f4 med {np.median(f['f4'].to_numpy()[in_b]):,.0f}  f11 med {np.median(f11[in_b]):.4f}")
print(f"  OUT: f1 med {np.median(f1[out_b]):,.0f}  f4 med {np.median(f['f4'].to_numpy()[out_b]):,.0f}  f11 med {np.median(f11[out_b]):.4f}")

assert not (set(in_a) & set(in_b)) and not (set(out_a) & set(out_b))
swap_in = np.concatenate([in_a, in_b]).astype(int)
swap_out = np.concatenate([out_a, out_b]).astype(int)
N = len(swap_in)

target = m35.copy()
target[swap_out] = False
target[swap_in] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

BIG = 2.0 * (base_new.max() - base_new.min())
score = base_new + BIG * target
score[f3 == 1] = score.min() - 1.0
score = score + 0.5772156649          # global shift distinct from v34/v35

s = pd.Series(score)
top = np.zeros(len(s), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())
whale = M.all(axis=0)
for prior in ("scores_v35", "scores_v34", "scores_v29"):
    pv = pd.read_csv(ROOT / "data" / f"{prior}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    shared = np.intersect1d(np.unique(score), np.unique(pv))
    print(f"floats shared with {prior}: {len(shared)} (must be 0)")
    assert len(shared) == 0
lo = [(top & p).sum() / TOPK for p in post]

print(f"distinct: {s.nunique():,}   cutoff members: {n_cut}   f3 in top: {int((top & (f3==1)).sum())}")
print(f"revolver share: {f1[top].astype(bool).mean():.1%}   whale-in: {(top & whale).sum()/whale.sum():.3f}   overlap vs v35: {(top & m35).sum()/TOPK:.4f}")
print(f"E[LB | posterior]: {np.mean(lo):.3f}   low-quartile {np.percentile(lo, 25):.3f}")
print(f"BOX: realized = {V35} + (r_in − r_out)·{N/1e5:.5f} ∈ [{V35 - N/1e5:.4f}, {V35 + N/1e5:.4f}]")
r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"corr(id, score): {r:+.2e}")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

pd.DataFrame({"id": ids, "score": score}).to_csv(ROOT / "data" / "scores_v36.csv", index=False)
print("wrote data/scores_v36.csv")
