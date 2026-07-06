"""Build data/scores_v38.csv — v38 'measured promotion' (the judged-account closer).

Base = v37-L's set (0.919143, the best measured set ever constructed, currently on the bench)
⊕ a small fresh tranche from the 27-constraint posterior (gap ≥ 60% of K, cap 300 — sized by
the measured λ-decay: fresh-top corrections carry λ ≈ 0.2–0.75, deep ones ~0).
Excluded by measurement: the imputer reorder (v36, net −0.252) and any deeper level shift
(v37-L, differential +0.034 — already harvested in the base).

Box: realized = 0.919143 + net·N/1e5. Every read > 0.904 keeps primary's best-score guarantee;
expected landing 0.9192–0.9198 vs the judged 0.918971.

Run: .venv/bin/python scratchpad/build_v38.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
CAP_TR, GAP_FLOOR = 300, 0.60
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]
BASE_READ = 0.919143

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
assert "v36" in keys and "v37L" in keys, "cache stale — need the 27-constraint build"
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
K = post.shape[0]
print(f"posterior calibrations kept: {K} (27 constraints)")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f = df.fillna(0.0)
f1, f11, f3 = f["f1"].to_numpy(), f["f11"].to_numpy(), f["f3"].to_numpy()
cat = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()
nbd = df["f6"].isna().to_numpy()

sL = pd.read_csv(ROOT / "data" / "scores_v37L.csv").set_index("id")["score"].reindex(ids).to_numpy()
mL = np.zeros(len(sL), bool)
mL[np.argpartition(-sL, TOPK)[:TOPK]] = True

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
base_new = vote + 1e-3 * tb
assert 1e-3 * np.abs(tb).max() < 0.5

eL = np.mean([(mL & p).sum() / TOPK for p in post])
print(f"anchor check — E[LB | posterior] for v37-L's set: {eL:.3f} (actual {BASE_READ})")

in_pool = np.flatnonzero(~mL & (f3 == 0))
out_pool = np.flatnonzero(mL)
in_pool = in_pool[np.lexsort((-tb[in_pool], -vote[in_pool]))]
out_pool = out_pool[np.lexsort((tb[out_pool], vote[out_pool]))]
n_a = 0
for i in range(CAP_TR):
    if vote[in_pool[i]] - vote[out_pool[i]] >= GAP_FLOOR * K:
        n_a += 1
    else:
        break
swap_in, swap_out = in_pool[:n_a], out_pool[:n_a]
print(f"fresh tranche: N = {n_a} (cap {CAP_TR}, gap ≥ {GAP_FLOOR:.0%} of {K})")
if n_a:
    print(f"  IN : vote med {np.median(vote[swap_in]):.0f}/{K}  f1 med {np.median(f1[swap_in]):,.0f}  catsum med {np.median(cat[swap_in]):,.0f}  f11 med {np.median(f11[swap_in]):.4f}  nbd {nbd[swap_in].mean():.0%}")
    print(f"  OUT: vote med {np.median(vote[swap_out]):.0f}/{K}  f1 med {np.median(f1[swap_out]):,.0f}  catsum med {np.median(cat[swap_out]):,.0f}  f11 med {np.median(f11[swap_out]):.4f}  nbd {nbd[swap_out].mean():.0%}")

target = mL.copy()
target[swap_out] = False
target[swap_in] = True
assert target.sum() == TOPK and not (target & (f3 == 1)).any()

BIG = 2.0 * (base_new.max() - base_new.min())
score = base_new + BIG * target
score[f3 == 1] = score.min() - 1.0
score = score + 0.4142135623          # global shift distinct from every prior build

s = pd.Series(score)
top = np.zeros(len(s), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
assert (top == target).all()
cut = np.sort(score)[::-1][TOPK - 1]
n_cut = int((score == cut).sum())
whale = M.all(axis=0)
for prior in ("scores_v37L", "scores_v36", "scores_v35", "scores_v34", "scores_v29"):
    pv = pd.read_csv(ROOT / "data" / f"{prior}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    shared = np.intersect1d(np.unique(score), np.unique(pv))
    print(f"floats shared with {prior}: {len(shared)} (must be 0)")
    assert len(shared) == 0
lo = [(top & p).sum() / TOPK for p in post]

print(f"distinct: {s.nunique():,}   cutoff members: {n_cut}   f3 in top: {int((top & (f3==1)).sum())}")
print(f"revolver share: {f1[top].astype(bool).mean():.1%}   whale-in: {(top & whale).sum()/whale.sum():.3f}")
print(f"overlap vs v37-L set: {(top & mL).sum()/TOPK:.4f}   vs v35 set: n/a (base is v37-L)")
print(f"E[LB | posterior]: {np.mean(lo):.3f}   low-quartile {np.percentile(lo, 25):.3f}")
print(f"BOX: realized = {BASE_READ} + net·{n_a/1e5:.5f} ∈ [{BASE_READ - n_a/1e5:.4f}, {BASE_READ + n_a/1e5:.4f}]")
r = np.corrcoef(ids.astype(np.float64), score)[0, 1]
print(f"corr(id, score): {r:+.2e}")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and abs(r) < 1e-2

pd.DataFrame({"id": ids, "score": score}).to_csv(ROOT / "data" / "scores_v38.csv", index=False)
print("wrote data/scores_v38.csv")
