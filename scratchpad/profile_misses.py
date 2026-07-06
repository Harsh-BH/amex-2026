"""Profile the estimated 'left users' — the ~8.1K truth-top members our banked set misses.

Best-available miss ranking over outsiders (f3=0 only; the hard evict is triple-validated):
blend of the 15-term posterior vote (25 cals, 27-constraint vintage) and the cluster-family
vote (4 cals), margin tie-break. v41's read measured the cluster-top 1,741 of these at
truth-rate ~ boundary-parity (net -0.076 vs weakest incumbents) -> the top of this ranking
is MEASURED to be ~20x enriched vs the 2% outsider base rate, so the profile is grounded,
not just model opinion. Compare: estimated misses vs weakest incumbents vs population.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
K = 100_000
N_MISS = 8_103   # 100K x (1 - 0.918971)

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
M = z["M"]
keys = [str(x) for x in z["obs_keys"]]
names = [str(x) for x in z["names"]]
print(f"cache: {M.shape[0]} masks ({'incl v41' if 'v41' in keys else 'pre-v41'})")

df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), z["ids"])

v15 = np.load(ROOT / "scratchpad" / "tri2_posterior_masks.npy").sum(0) / 25.0
vCL = np.load(ROOT / "scratchpad" / "tri3_posterior_masks.npy").sum(0) / 4.0
w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = [names.index(n) for n in ("z1", "z7", "z9", "z10", "exl", "f3neg")]
margin_r = pd.Series((z["T"][:, SIX] @ w6.astype(np.float32)).astype(np.float64)).rank(pct=True).to_numpy()

s35 = pd.read_csv(ROOT / "data" / "scores_v35.csv").set_index("id")["score"].reindex(df["id"]).to_numpy()
S = np.zeros(len(df), bool)
S[np.argpartition(-s35, K)[:K]] = True
f3 = df["f3"].fillna(0).to_numpy()

blend = 0.5 * v15 + 0.5 * vCL + 1e-6 * margin_r
out_ok = np.flatnonzero(~S & (f3 == 0))
est_miss = out_ok[np.argpartition(-blend[out_ok], N_MISS)[:N_MISS]]
in_idx = np.flatnonzero(S)
weakest_in = in_idx[np.argpartition(blend[in_idx], N_MISS)[:N_MISS]]

cat = df[["f6", "f7", "f8", "f9", "f10"]].fillna(0).sum(axis=1).to_numpy()
feat = {
    "f1 revolve $": df["f1"].fillna(0).to_numpy(),
    "catsum $": cat,
    "f5 'total' ": df["f5"].fillna(0).to_numpy(),
    "f4 points": df["f4"].fillna(0).to_numpy(),
    "f21 redeemed": df["f21"].fillna(0).to_numpy(),
    "f19 supp": df["f19"].fillna(0).to_numpy(),
    "f20 cards": df["f20"].fillna(0).to_numpy(),
    "f22 emails": df["f22"].fillna(0).to_numpy(),
    "f12 logins": df["f12"].fillna(0).to_numpy(),
    "f11 risk": df["f11"].fillna(0).to_numpy(),
    "f17 line $": df["f17"].fillna(0).to_numpy(),
}
flags = {
    "revolver (f1>0)": df["f1"].fillna(0).to_numpy() > 0,
    "nbd (f6 miss)": df["f6"].isna().to_numpy(),
    "rewards-inactive": df["f4"].isna().to_numpy(),
    "has lend line": df["f17"].notna().to_numpy(),
    "f2>0 calls": df["f2"].fillna(0).to_numpy() > 0,
}

groups = {"EST-MISS (left users)": est_miss, "WEAKEST-IN (their seats)": weakest_in,
          "POPULATION": np.arange(len(df))}
print(f"\n{'':24}" + "".join(f"{g:>26}" for g in groups))
for nm, v in feat.items():
    print(f"{nm:24}" + "".join(f"{np.median(v[ix]):>26,.1f}" for ix in groups.values()))
for nm, v in flags.items():
    print(f"{nm:24}" + "".join(f"{v[ix].mean():>25.1%} " for ix in groups.values()))

# vote-band + measurement status of the estimated misses
v41_ins = None
if (ROOT / "data" / "scores_v41.csv").exists():
    s41 = pd.read_csv(ROOT / "data" / "scores_v41.csv").set_index("id")["score"].reindex(df["id"]).to_numpy()
    m41 = np.zeros(len(df), bool)
    m41[np.argpartition(-s41, K)[:K]] = True
    v41_ins = m41 & ~S
em = np.zeros(len(df), bool)
em[est_miss] = True
never = ~M.any(axis=0)
print(f"\nestimated-miss composition:")
print(f"  measured by v41's read (engagement pool):     {int((em & v41_ins).sum()):>6,}" if v41_ins is not None else "")
print(f"  never inside ANY of the {M.shape[0]} submitted top sets: {int((em & never).sum()):>6,}")
print(f"  15-term vote bands: 0 votes {int((em & (v15==0)).sum()):,} | 1-12 {int((em & (v15>0) & (v15<=0.5)).sum()):,} | 13-24 {int((em & (v15>0.5) & (v15<1)).sum()):,}")
print(f"  cluster vote 4/4: {int((em & (vCL==1.0)).sum()):,}   0/4: {int((em & (vCL==0)).sum()):,}")
# spend-band structure of the misses vs their seats
qs = np.quantile(cat[in_idx], [0.25, 0.5, 0.75])
print(f"\n  catsum quartile cuts of the CURRENT top set: {qs.round(0)}")
for lbl, ix in (("EST-MISS", est_miss), ("WEAKEST-IN", weakest_in)):
    shares = [float((cat[ix] < qs[0]).mean()), float(((cat[ix] >= qs[0]) & (cat[ix] < qs[2])).mean()),
              float((cat[ix] >= qs[2]).mean())]
    print(f"  {lbl:10} below-Q1 {shares[0]:.0%} | Q1-Q3 {shares[1]:.0%} | above-Q3 {shares[2]:.0%}")
