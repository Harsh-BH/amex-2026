"""Thread 3d: the f17-miss subset-of-f18-miss anomaly (17,190 rows have f18 missing but f17 present)
-- decode what this means. Also check tiny-missing features f1/f2/f3/f19/f20 (0% or near-0%) for structure."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
import numpy as np
import pandas as pd
df = PremierEDA().df

miss = df[[f"f{i}" for i in range(1,24)]].isna()
gap_mask = (~miss["f17"]) & (miss["f18"])   # f17 present, f18 missing
print(f"f17 present & f18 missing: n={gap_mask.sum()} ({gap_mask.mean():.2%})")
sub = df.loc[gap_mask]
print(f"  mean f17={sub['f17'].mean():.1f}  mean f1={sub['f1'].mean():.1f}  mean f19={sub['f19'].mean():.2f}")
print(f"  -> hypothesis: member has a TOTAL lend line but NO consumer-specific lend sub-line (e.g. small-business card variant)")
print(f"  f19 dist: {sub['f19'].value_counts(normalize=True).round(3).to_dict()}")
others = df.loc[~gap_mask & ~miss['f17']]
print(f"  vs f17-present & f18-present group f19 dist: {others['f19'].value_counts(normalize=True).round(3).to_dict()}")

print("\n=== f20 (active charge cards) -- only 0.02% missing (101 rows). What are they? ===")
m20 = miss["f20"]
print(f"  n={m20.sum()}")
sub20 = df.loc[m20]
print(sub20[["f1","f2","f3","f5","f11","f19"]].describe())

print("\n=== f19 (supp accounts) -- 0.00% missing per feature-notes but let's verify with exact count ===")
print(f"  f19 missing count: {miss['f19'].sum()}")

print("\n=== f12 (logins) 5% missing -- correlate with f22 (email-open) missingness? ===")
print(f"  f12-miss & f22-miss joint: observed={(miss['f12']&miss['f22']).mean():.4f} chance={miss['f12'].mean()*miss['f22'].mean():.4f}")
print(f"  -> ratio {(miss['f12']&miss['f22']).mean()/(miss['f12'].mean()*miss['f22'].mean()):.2f}")

print("\n=== f11 (risk score) 0.50% missing -- who are they? ===")
m11 = miss["f11"]
sub11 = df.loc[m11]
print(f"  n={m11.sum()}")
print(sub11[["f1","f2","f3","f5"]].describe())
print(f"  f3=1 share in f11-missing cohort: {(sub11['f3'].fillna(0)==1).mean():.2%}  (pop avg 10.9%)")
