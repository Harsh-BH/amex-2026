"""Build data/scores_v28.csv — v28 'recovered-consensus-r2' (the 19-constraint refit's consensus).

Same construction as v27, from the REFIT artifacts: majority vote across the kept posterior
calibrations (now conditioned on v27's actual 0.895 read), tie-broken by the refit 6-term P&L
margin, hard f3 screen. float64 throughout. v27 artifacts are frozen in scratchpad/v27_frozen/.

Run: .venv/bin/python scratchpad/build_v28.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TOPK = 100_000
SIX = ["z1", "z7", "z9", "z10", "exl", "f3neg"]

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
T, M, ids = z["T"], z["M"], z["ids"]
names = [str(x) for x in z["names"]]
keys = [str(x) for x in z["obs_keys"]]
assert "v27" in keys, "cache is stale — rebuild with the 19-constraint OBS"
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
print(f"posterior calibrations: {post.shape[0]}  (v27 used 12; refit keeps its own count)")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all()
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()

vote = post.sum(axis=0).astype(np.float64)
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6
tb = margin / margin.std()
score = vote + 1e-3 * tb
assert 1e-3 * np.abs(tb).max() < 0.5, "tiebreak crosses vote levels"
score[f3 == 1] = score.min() - 1.0

s = pd.Series(score)
top = np.zeros(len(s), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
cut = np.sort(score)[::-1][TOPK - 1]
whale = M.all(axis=0)
v24 = M[keys.index("v24")]
v27 = M[keys.index("v27")]
n_cut = int((score == cut).sum())
elb = np.mean([(top & p).sum() / TOPK for p in post])

print(f"distinct scores: {s.nunique():,}")
print(f"members at cutoff: {n_cut} (must be 1)")
print(f"f3=1 in top-20%: {int((top & (f3 == 1)).sum())} (must be 0)")
print(f"revolver share: {f1[top].astype(bool).mean():.1%}   whale-in: {(top & whale).sum() / whale.sum():.3f}")
print(f"overlap vs v27: {(top & v27).sum() / TOPK:.3f}   vs v24: {(top & v24).sum() / TOPK:.3f}")
print(f"E[LB | refit posterior]: {elb:.3f}")
# profile of the members v28 bets on vs v27 (the economic story of the correction)
gain = top & ~v27
lose = v27 & ~top
cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()
for nm, m in (("IN (new vs v27)", gain), ("OUT (dropped)", lose)):
    print(f"  {nm}: n={m.sum():,}  f1 med {np.median(f1[m]):,.0f}  revolver {f1[m].astype(bool).mean():.0%}"
          f"  catsum med {np.median(cat[m]):,.0f}  f11 med {np.median(df['f11'].fillna(0).to_numpy()[m]):.4f}")
assert len(s) == 500_000 and s.notna().all() and n_cut == 1 and int((top & (f3 == 1)).sum()) == 0

out = ROOT / "data" / "scores_v28.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
