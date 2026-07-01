"""Verify the exact-equality hits are chance artifacts of low-cardinality binary features,
EXCEPT the genuinely interesting f17~f18 (continuous, 11% exact) which is a real near-duplicate signal."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA
import numpy as np
import pandas as pd
df = PremierEDA().df

print("=== cardinality of each feature (continuous vs binary/low-card) ===")
for c in [f"f{i}" for i in range(1,24)]:
    nu = df[c].nunique()
    print(f"  {c}: nunique={nu}")

print("\n=== f2 vs f3 (BOTH binary 0/1) -- chance-expected equality rate ===")
sub = df[["f2","f3"]].fillna(0)
p2 = sub["f2"].mean(); p3 = sub["f3"].mean()
chance_eq = p2*p3 + (1-p2)*(1-p3)
actual_eq = (sub["f2"]==sub["f3"]).mean()
print(f"  P(f2=1)={p2:.3f}  P(f3=1)={p3:.3f}  chance-equal (if independent)={chance_eq:.3f}  actual={actual_eq:.3f}")
# proper test: mutual information / phi coefficient
ct = pd.crosstab(sub["f2"], sub["f3"])
print(ct)
n = len(sub)
phi = (ct.loc[1,1]*ct.loc[0,0] - ct.loc[1,0]*ct.loc[0,1]) / np.sqrt((ct.loc[1,1]+ct.loc[1,0])*(ct.loc[0,1]+ct.loc[0,0])*(ct.loc[1,1]+ct.loc[0,1])*(ct.loc[1,0]+ct.loc[0,0]))
print(f"  phi coefficient (binary correlation): {phi:.4f}  (near 0 = independent despite high raw-equality%)")

print("\n=== f3==1 -> f2 distribution (does collection-call NOT imply cancel-call?) ===")
print(sub.loc[sub["f3"]==1, "f2"].value_counts(normalize=True))
print("=== f2==1 -> f3 distribution ===")
print(sub.loc[sub["f2"]==1, "f3"].value_counts(normalize=True))
print(" -> if these were the SAME underlying event encoded twice we'd see near-100% co-occurrence; we see near independence (phi tells the real story)")

print("\n=== Re-check f17~f18 -- the ONLY high-cardinality pair with notable exact-match (11%) ===")
sub2 = df[["f17","f18"]].dropna()
exact = np.isclose(sub2["f17"], sub2["f18"])
print(f"  n={len(sub2)}  f17==f18 exact: {exact.mean():.2%}")
# what's special about the f17==f18 subgroup vs not?
print(f"  f17==f18 group: f19 dist: {df.loc[sub2.index[exact],'f19'].value_counts(normalize=True).round(3).to_dict()}")
print(f"  f17!=f18 group: f19 dist: {df.loc[sub2.index[~exact],'f19'].value_counts(normalize=True).round(3).to_dict()}")
print("  -> hypothesis: f17==f18 when member has NO non-consumer (e.g. business) credit, i.e. consumer lend line IS the whole lend line")
