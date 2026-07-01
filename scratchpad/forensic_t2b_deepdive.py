"""Thread 2 deep-dive: f19/f20 structure, f1~f11 functional form, f22/f23, exact-equality scan."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
import numpy as np
import pandas as pd
df = PremierEDA().df

print("=== A. f19 (supp accts, 1-4) vs f20 (active charge cards, 1-2) -- is f20 a deterministic func of f19? ===")
sub = df[["f19","f20"]].dropna()
for v in sorted(sub["f19"].unique()):
    g = sub.loc[sub["f19"]==v, "f20"]
    print(f"  f19={v}: n={len(g)}  f20 dist: {g.value_counts(normalize=True).round(3).to_dict()}")
print("  -> NOT deterministic; looks like roughly independent noisy categorical, f20=2 share rises with f19")

print("\n=== B. f1~f11 functional form -- f11 risk score vs f1 revolve balance: is f11 = f(f1)? ===")
sub2 = df[["f1","f11"]].dropna()
# bin f1 into deciles, look at f11 mean+std per bin
sub2["f1_bin"] = pd.qcut(sub2["f1"], 10, duplicates="drop")
g = sub2.groupby("f1_bin")["f11"].agg(["mean","std","count"])
print(g)
# is f11 ever EXACTLY a multiple/fraction of f1? check f11*f1 and f11/f1-style transforms for a constant
nz = sub2[sub2["f1"]>0].copy()
nz["ratio"] = nz["f11"]/nz["f1"]
print(f"  f11/f1 (f1>0): mean={nz['ratio'].mean():.6f} std={nz['ratio'].std():.6f} cv={nz['ratio'].std()/nz['ratio'].mean():.2f}")
print(f"  f1==0 rate: {(sub2['f1']==0).mean():.1%}; mean f11 in that group: {sub2.loc[sub2['f1']==0,'f11'].mean():.5f}")
print(f"  f1>0 rate: {(sub2['f1']>0).mean():.1%}; mean f11 in that group: {sub2.loc[sub2['f1']>0,'f11'].mean():.5f}")

print("\n=== C. f22 (emails opened, 0-15) / f23 (emails clicked, 1-3, 88% missing) structure ===")
sub3 = df[["f22","f23"]].dropna()
print(f"  n={len(sub3)} (both present)")
print(f"  f23 unique: {sorted(sub3['f23'].unique())}")
ct = pd.crosstab(pd.qcut(sub3["f22"], 5, duplicates="drop"), sub3["f23"])
print(ct)
print(f"  corr f22~f23 spearman: {sub3['f22'].corr(sub3['f23'], method='spearman'):.4f}")
# does f23 presence depend on f22 value? (missingness signal)
df["f23_present"] = df["f23"].notna().astype(int)
print(f"  f23 presence rate by f22 quintile:")
df_f22 = df[["f22","f23_present"]].dropna(subset=["f22"])
df_f22["f22_bin"] = pd.qcut(df_f22["f22"], 5, duplicates="drop")
print(df_f22.groupby("f22_bin")["f23_present"].mean())

print("\n=== D. systematic near-exact-equality scan: for every pair, fraction of rows where a==b (raw, no scale) ===")
FEATS = [f"f{i}" for i in range(1,24)]
found = []
for i,a in enumerate(FEATS):
    for b in FEATS[i+1:]:
        sub = df[[a,b]].dropna()
        if len(sub) < 1000: continue
        eq = np.isclose(sub[a], sub[b], rtol=1e-6, atol=1e-6)
        if eq.mean() > 0.005:  # >0.5% exact equal is notable for continuous features
            found.append((a,b,eq.mean(),len(sub)))
found.sort(key=lambda x:-x[2])
for a,b,r,n in found:
    print(f"  {a}=={b} exactly: {r:.2%} of {n} non-null rows")
if not found:
    print("  none found above 0.5% threshold")

print("\n=== E. check linear combos: does f17-f18 (lend line minus consumer-lend line) relate to anything? ===")
sub4 = df[["f17","f18"]].dropna()
diff = sub4["f17"] - sub4["f18"]
print(f"  f17-f18: mean={diff.mean():.1f} std={diff.std():.1f} min={diff.min():.1f} max={diff.max():.1f}")
print(f"  f17-f18 < 0 (consumer line EXCEEDS total line): {(diff<0).mean():.2%}")
print(f"  f17==f18 exactly: {(diff==0).mean():.2%}")
