"""Thread 2d: chase two specific data anomalies as potential decoding clues:
(1) f18 > f17 in 36.5% of cases (consumer lend line EXCEEDING total lend line - should be impossible if f18 subset f17)
(2) f16's floor (8.9, not 0) -- is f16 actually a PERCENTAGE/RATE not a dollar amount?"""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA
import numpy as np
import pandas as pd
df = PremierEDA().df

print("=== A. f18 > f17 anomaly -- decompose by how much ===")
sub = df[["f17","f18","f19","f1"]].dropna(subset=["f17","f18"])
exceed = sub["f18"] > sub["f17"]
print(f"  f18>f17: n={exceed.sum()} ({exceed.mean():.1%})")
print(f"  among exceeders: mean excess = {(sub.loc[exceed,'f18']-sub.loc[exceed,'f17']).mean():.1f}, "
      f"max excess={(sub.loc[exceed,'f18']-sub.loc[exceed,'f17']).max():.1f}")
print(f"  excess as % of f17: mean={((sub.loc[exceed,'f18']-sub.loc[exceed,'f17'])/sub.loc[exceed,'f17']).mean():.2%}")
print(f"  -> if small (<5%) consistently, likely ROUNDING/noise in two independently-estimated lines, not a hard subset relationship")
print(f"  f19 dist among exceeders vs non: exceed={sub.loc[exceed,'f19'].value_counts(normalize=True).round(3).to_dict()}")
print(f"                                    non-exceed={sub.loc[~exceed,'f19'].value_counts(normalize=True).round(3).to_dict()}")

print("\n=== B. f16 floor structure (claimed non-zero floor ~8.9) ===")
f16 = df["f16"].dropna()
print(f"  f16 stats: min={f16.min():.4f} max={f16.max():.4f} n_unique={f16.nunique()}")
print(f"  f16 histogram (20 bins):")
hist, edges = np.histogram(f16, bins=20)
for h, e0, e1 in zip(hist, edges[:-1], edges[1:]):
    print(f"    [{e0:7.2f},{e1:7.2f}): {h:6d} {'#'*int(h/2000)}")
print(f"  bottom 10 smallest unique values: {sorted(f16.unique())[:10]}")
print(f"  is f16 maybe a PERCENT (0-100 scale, dollar credit used = pct * some base)? max={f16.max():.2f} is suspiciously close to 64.4 not 100")
print(f"  f16 vs f14 (airline credits 0-200) scale comparison -- f14 mean={df['f14'].mean():.1f} max={df['f14'].max():.1f}")
print(f"  f16/f14 ratio (where f14>0): mean={ (df['f16']/df['f14'].replace(0,np.nan)).mean():.4f}")

print("\n=== C. f13 (lounge access 0-3) -- discrete, check if it's TRULY capped at 3 or if 3 is a '3+' bucket ===")
f13 = df["f13"].dropna()
print(f"  f13 value counts: {f13.value_counts().sort_index().to_dict()}")
print(f"  -> if count at 3 is anomalously large vs the decay pattern of 0,1,2, it's likely a censored '3+' bucket")
