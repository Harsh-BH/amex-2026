"""Deep dive f1~f11 (Spearman 0.577, much higher than Pearson 0.196 -- strongly nonlinear monotonic).
Is f11 = g(f1) + noise for some functional g? Check rank-transform fit quality and whether residual carries info."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA
import numpy as np
import pandas as pd
df = PremierEDA().df

sub = df[["f1","f11"]].dropna().copy()
print(f"n={len(sub)}")
sub["f1_rank_pct"] = sub["f1"].rank(pct=True)
sub["f11_rank_pct"] = sub["f11"].rank(pct=True)

# bin f1 into 50 percentile bins, see f11 mean+std (functional form check)
sub["bin"] = pd.qcut(sub["f1_rank_pct"], 20, labels=False, duplicates="drop")
g = sub.groupby("bin").agg(f1_mean=("f1","mean"), f11_mean=("f11","mean"), f11_std=("f11","std"), n=("f11","size"))
print(g.to_string())

print(f"\nNote: f1=0 for 53.2% of rows (a point mass). The f1~f11 relationship may be entirely driven by")
print(f"the f1==0 vs f1>0 SPLIT (transactor vs revolver), not a continuous functional form within each side.")
print(f"f1==0 group: f11 mean={sub.loc[sub['f1']==0,'f11'].mean():.5f} median={sub.loc[sub['f1']==0,'f11'].median():.5f}")
print(f"f1>0 group: f11 mean={sub.loc[sub['f1']>0,'f11'].mean():.5f} median={sub.loc[sub['f1']>0,'f11'].median():.5f}")
sub2 = sub[sub["f1"]>0].copy()
print(f"\nWITHIN f1>0 only: spearman(f1,f11) = {sub2['f1'].corr(sub2['f11'], method='spearman'):.4f}")
sub2["bin2"] = pd.qcut(sub2["f1"], 10, duplicates="drop")
print(sub2.groupby("bin2")["f11"].agg(["mean","std","count"]))
