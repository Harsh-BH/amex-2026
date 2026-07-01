"""Identify WHAT the two giant tie-groups (54304 @ min-1, 41779 @ 0.0) actually are."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
import numpy as np
import pandas as pd

df = PremierEDA().df
s19 = dollar_profit_v19_lending(df).to_numpy()

vals, counts = np.unique(s19, return_counts=True)
g1_val = vals[np.argmax(counts)]          # the -1.005481 group (54304)
order_c = np.argsort(-counts)
g2_val = vals[order_c[1]]                  # the 0.0 group (41779)

m1 = (s19 == g1_val)
m2 = (s19 == g2_val)
print(f"group1 (n={m1.sum()}, val={g1_val:.4f}): f3==1 share = {(df['f3'].fillna(0)==1)[m1].mean():.1%}")
print(f"  -> this is the f3-distress-evict floor (s.min()-1), confirms the existing 'evict to floor' mechanic")

print(f"\ngroup2 (n={m2.sum()}, val={g2_val:.4f}):")
for c in ["f1","f4","f5","f6","f7","f8","f9","f10","f11","f17","f3"]:
    sub = df[c].to_numpy(float)[m2]
    nan_rate = np.isnan(sub).mean()
    print(f"  {c}: nan_rate={nan_rate:.1%}  nonnan_mean={np.nanmean(sub) if not np.all(np.isnan(sub)) else float('nan'):.3f}  nonnan_allzero={np.nanmax(sub)==0 if not np.all(np.isnan(sub)) else 'allnan'}")

# is group2 simply "all relevant raw features are 0 or NaN" -> the true floor of legit (non-evicted) members?
f3ok = (df['f3'].fillna(0)==1)
print(f"\ngroup2 f3==1 share: {f3ok[m2].mean():.2%} (should be ~0, since those get evicted to group1 instead)")
