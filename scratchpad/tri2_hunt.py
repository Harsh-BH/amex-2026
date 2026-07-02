"""Directed missing-term hunt. The pack at 0.925-0.929 proves ~+0.010 is findable; the family's
systematic strain on the six early constraints (v1,v2,v3,v4,v6,v8; +/-0.004-0.005 = 2-3x noise)
is the only unexplained variance left. This script asks: WHAT member-type, if re-scored, would
fix all six residuals at once?

Method: target g_i = -sum_k r_k*(m_ki - mean_k) over the strained constraints, restricted to
contested members (posterior vote in the middle band) — the direction the truth demotes/promotes
relative to the family. Then correlate g against features & transforms. A coherent feature
pattern = the missing term, to be added to the family and re-fit.
Run: cd scratchpad && ../.venv/bin/python tri2_hunt.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triangulate2 as t2

T, M, ids, names, keys = t2.load()
post = np.load(t2.ROOT / "scratchpad" / "tri2_posterior_masks.npy")
K = post.shape[0]
vote = post.sum(0)
df = pd.read_pickle(t2.ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)

# strained constraints and their mean residuals (posterior - observed), from tri2_falsify part A
STRAIN = {"v1": +0.0053, "v2": +0.0038, "v3": +0.0035, "v4": -0.0041, "v6": +0.0047, "v8": -0.0044}
g = np.zeros(M.shape[1])
for k, r in STRAIN.items():
    m = M[keys.index(k)].astype(float)
    g -= r * (m - m.mean())
band = (vote >= 5) & (vote <= K - 5)                  # contested members only
print(f"contested band: {band.sum():,} members; g std in band {g[band].std():.5f}")

f = df.fillna(0.0)
cands = {}
for c in [f"f{i}" for i in range(1, 24)]:
    v = f[c].to_numpy(float)
    cands[c] = v
    if v.min() >= 0 and v.max() > 50:
        cands[f"log_{c}"] = np.log1p(v)
cands["catsum"] = f[["f6", "f7", "f8", "f9", "f10"]].sum(axis=1).to_numpy()
cands["nbd"] = df["f6"].isna().to_numpy(float)
cands["travel_share"] = (f["f6"] + f["f9"]).to_numpy() / np.maximum(cands["catsum"], 1)
cands["spend_per_card"] = cands["catsum"] / np.maximum(f["f20"].to_numpy(), 1)
cands["f1_x_f11"] = (f["f1"] * f["f11"]).to_numpy()
cands["util"] = np.where(f["f17"].to_numpy() > 0, f["f1"].to_numpy() / np.maximum(f["f17"].to_numpy(), 1), 0)
cands["f4_per_spend"] = f["f4"].to_numpy() / np.maximum(cands["catsum"], 1)
cands["redeem_rate"] = f["f21"].to_numpy() / np.maximum((f["f21"] + f["f4"]).to_numpy(), 1)

gb = g[band]
gb = (gb - gb.mean()) / gb.std()
rows = []
for name, v in cands.items():
    vb = v[band]
    sd = vb.std()
    if sd < 1e-12:
        continue
    r_p = float(np.corrcoef(gb, (vb - vb.mean()) / sd)[0, 1])
    rows.append((name, r_p))
rows.sort(key=lambda x: -abs(x[1]))
print("\ntop feature correlates of the fix-direction (contested band):")
for name, r_p in rows[:15]:
    print(f"  {name:<16} r={r_p:+.4f}")
