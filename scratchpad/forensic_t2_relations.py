"""Forensic Thread 2: EXACT/near-exact feature relationships -> decoding clues.
Test for: fixed ratios, sums, exact equalities, conditional determinism (e.g. for SOME subpopulation).
"""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
import numpy as np
import pandas as pd

df = PremierEDA().df
FEATS = [f"f{i}" for i in range(1, 24)]

print("=== A. Pairwise Pearson + Spearman correlation matrix (full, pairwise non-null) ===")
corr_p = df[FEATS].corr(method="pearson")
corr_s = df[FEATS].corr(method="spearman")
# print only |r|>0.5 pairs (excluding self / already-known f17~f18, spend-cat collinearity)
pairs = []
for i, a in enumerate(FEATS):
    for b in FEATS[i+1:]:
        rp, rs = corr_p.loc[a, b], corr_s.loc[a, b]
        if abs(rp) > 0.5 or abs(rs) > 0.5:
            pairs.append((a, b, rp, rs))
pairs.sort(key=lambda x: -abs(x[3]))
for a, b, rp, rs in pairs:
    print(f"  {a:>4} ~ {b:<4}  pearson={rp:+.3f}  spearman={rs:+.3f}")

print("\n=== B. f17 vs f18 fixed-ratio check (A4: f18 subset of f17) ===")
sub = df[["f17", "f18"]].dropna()
ratio = sub["f18"] / sub["f17"]
print(f"  n={len(sub)}  ratio f18/f17: mean={ratio.mean():.4f} std={ratio.std():.4f} "
      f"min={ratio.min():.4f} max={ratio.max():.4f}")
print(f"  ratio==1.0 (f18==f17 exactly): {(ratio==1.0).mean():.1%}")
print(f"  f18<=f17 always?: {(sub['f18']<=sub['f17']+1e-6).mean():.1%}")
vc = ratio.round(3).value_counts().head(10)
print(f"  top rounded-ratio values:\n{vc}")

print("\n=== C. f5 'Total Spend' exact-relationship probes (A1/A14 says it's NOT sum of f6-f10) ===")
sub2 = df[["f5", "f6", "f7", "f8", "f9", "f10"]].dropna()
catsum = sub2[SPEND_CATS].sum(axis=1)
print(f"  n={len(sub2)}  corr(f5, catsum) pearson={sub2['f5'].corr(catsum):.4f}  spearman={sub2['f5'].corr(catsum, method='spearman'):.4f}")
for scale in [1, 0.1, 0.01, 1/12, 1/52, 1/365]:
    resid = (sub2['f5'] - catsum*scale)
    print(f"  scale={scale:.4f}: mean|resid|={resid.abs().mean():.1f}  exact-match(tol=1)={(resid.abs()<1).mean():.2%}")
# maybe f5 relates to ONE category only?
for c in SPEND_CATS:
    print(f"  corr(f5, {c}) spearman={sub2['f5'].corr(sub2[c], method='spearman'):.4f}")

print("\n=== D. f4/f21 rewards-points relationship (points balance vs redeemed) ===")
sub3 = df[["f4", "f21"]].dropna()
print(f"  n={len(sub3)}  corr f4~f21 pearson={sub3['f4'].corr(sub3['f21']):.4f} spearman={sub3['f4'].corr(sub3['f21'], method='spearman'):.4f}")
ratio2 = sub3["f21"] / (sub3["f4"] + sub3["f21"])
print(f"  redemption_intensity=f21/(f4+f21): mean={ratio2.mean():.4f} std={ratio2.std():.4f}")
print(f"  f21 > f4 ever? {(sub3['f21']>sub3['f4']).mean():.2%}")
print(f"  f21 == 0 exactly: {(sub3['f21']==0).mean():.2%}")

print("\n=== E. f11 risk score vs f1 revolve balance / f3 collection-calls exact structure ===")
sub4 = df[["f11", "f1", "f3"]].dropna()
print(f"  corr f11~f1: pearson={sub4['f11'].corr(sub4['f1']):.4f}")
print(f"  f11 by f3 group: f3=0 mean={df.loc[df['f3'].fillna(0)==0,'f11'].mean():.4f}  f3=1 mean={df.loc[df['f3'].fillna(0)==1,'f11'].mean():.4f}")
print(f"  f11 unique values count: {df['f11'].nunique()}  (continuous? sample: {sorted(df['f11'].dropna().unique())[:10]})")

print("\n=== F. f2/f3 relationship (cancellation calls vs collection calls -- is f3 subset of f2?) ===")
sub5 = df[["f2", "f3"]].fillna(0)
ct = pd.crosstab(sub5["f2"], sub5["f3"])
print(ct)
print(f"  f3=1 implies f2=1 always? {(sub5.loc[sub5['f3']==1,'f2']==1).mean():.2%}")

print("\n=== G. f19/f20 (supp accounts / active charge cards) exact structure ===")
sub6 = df[["f19", "f20"]].dropna()
print(f"  f19 unique: {sorted(sub6['f19'].unique())}")
print(f"  f20 unique: {sorted(sub6['f20'].unique())}")
ct2 = pd.crosstab(sub6["f19"], sub6["f20"])
print(ct2)

print("\n=== H. f13-f16 benefit-usage internal relationships ===")
sub7 = df[["f13","f14","f15","f16"]].dropna()
print(sub7.corr(method="spearman"))
print(f"f13 (lounge count) unique: {sorted(sub7['f13'].unique())}")
print(f"f15 (cab months 0-11) unique: {sorted(sub7['f15'].unique())}")

