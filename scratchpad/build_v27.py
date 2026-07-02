"""Build data/scores_v27.csv — the v27 'recovered-consensus' ranking (float64-clean).

v27 = majority vote across the 12 kept Triangulation-2.0 posterior calibrations (masks saved by
`triangulate2.py posterior`, deterministic seeds 42..57), tie-broken WITHIN vote levels by the
recovered 6-term P&L margin (fit6, the best single calibration), plus the LB-validated hard f3
collection screen. Rebuilt here in float64 because the first consensus CSV was float32 and its
quantized tiebreak created arbitrary tie groups at the top-20% boundary (caught by the cutoff
-uniqueness guard; 3 members shared the cutoff value, hundreds tied in the 99-101K band).

Provenance: triangulate2.py build -> posterior (masks) + tri2_fit6.py (w6) -> this script.
Run: .venv/bin/python scratchpad/build_v27.py
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
post = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy")
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert (df["id"].to_numpy() == ids).all(), "id order mismatch"
f3 = df["f3"].fillna(0).to_numpy()
f1 = df["f1"].fillna(0).to_numpy()

vote = post.sum(axis=0).astype(np.float64)                       # 0..12 posterior membership votes
margin = (T[:, [names.index(k) for k in SIX]].astype(np.float64)) @ w6   # recovered P&L margin (float64)
tb = margin / margin.std()
score = vote + 1e-3 * tb                                          # tiebreak never crosses a vote step
assert 1e-3 * (np.abs(tb).max()) < 0.5, "tiebreak crosses vote levels"
score[f3 == 1] = score.min() - 1.0                                # hard collection screen (v11min-validated)

s = pd.Series(score)
top = np.zeros(len(s), bool)
top[np.argpartition(-score, TOPK)[:TOPK]] = True
cut = np.sort(score)[::-1][TOPK - 1]
whale = M.all(axis=0)
v24 = M[keys.index("v24")]

n_cut = int((score == cut).sum())
elb = np.mean([(top & p).sum() / TOPK for p in post])
print(f"distinct scores: {s.nunique():,}")
print(f"members at the cutoff value: {n_cut} (must be 1)")
print(f"f3=1 in top-20%: {int((top & (f3 == 1)).sum())} (must be 0)")
print(f"revolver share of top-20%: {f1[top].astype(bool).mean():.1%}")
print(f"whale in-rate: {(top & whale).sum() / whale.sum():.3f}")
print(f"overlap vs v24: {(top & v24).sum() / TOPK:.3f}")
print(f"E[LB | posterior]: {elb:.3f}")
assert len(s) == 500_000 and s.notna().all()
assert n_cut == 1 and int((top & (f3 == 1)).sum()) == 0

out = ROOT / "data" / "scores_v27.csv"
pd.DataFrame({"id": ids, "score": score}).to_csv(out, index=False)
print(f"wrote {out.relative_to(ROOT)}")
