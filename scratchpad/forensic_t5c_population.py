"""Thread 5c: characterize WHO is in the disjoint-feature top-20% populations (f2,f3,f11,f19/f20) --
are they a coherent alternate "whale" population we're missing, or just noise/risk populations
that genuinely don't belong (sanity-confirming v19's choice)?"""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
from lb_predict import LBPredictor, TOP
import numpy as np
import pandas as pd

df = PremierEDA().df
ids = df["id"].to_numpy()
s19 = dollar_profit_v19_lending(df).to_numpy()
p = LBPredictor(ids=ids)
f = df.fillna(0.0)
catsum = f[SPEND_CATS].sum(axis=1).to_numpy()

for feat in ["f2", "f3", "f11", "f19", "f20"]:
    v = f[feat].to_numpy(float)
    top_idx = np.argpartition(-v, TOP)[:TOP]
    print(f"=== top-20%-by-{feat} (n={TOP}) profile ===")
    print(f"  mean catsum={catsum[top_idx].mean():.0f} (pop {catsum.mean():.0f}, ratio {catsum[top_idx].mean()/catsum.mean():.2f}x)")
    print(f"  mean f1={f['f1'].to_numpy()[top_idx].mean():.0f} (pop {f['f1'].mean():.0f}, ratio {f['f1'].to_numpy()[top_idx].mean()/f['f1'].mean():.2f}x)")
    print(f"  mean f11={f['f11'].to_numpy()[top_idx].mean():.4f} (pop {f['f11'].mean():.4f}, ratio {f['f11'].to_numpy()[top_idx].mean()/f['f11'].mean():.2f}x)")
    print(f"  v19 score mean={s19[top_idx].mean():.3f} (pop {s19.mean():.3f}, v19's own top20 mean would be near +5)")
    print()

print("=== are f19=4 (max supp accounts) members systematically high or low value? (the A18 negative-corr check, restated) ===")
for v19val in [1,2,3,4]:
    mask = (f["f19"].to_numpy() == v19val)
    print(f"  f19={v19val}: n={mask.sum()}  mean catsum={catsum[mask].mean():.0f}  mean v19score={s19[mask].mean():.3f}  top20-rate={ (np.isin(np.where(mask)[0], np.argpartition(-s19,TOP)[:TOP])).mean():.2%}")

print("\n=== multiplicative form sanity: does MULTIPLYING catsum * f1 (instead of v19's additive z-sum) select a meaningfully different top-20%? ===")
mult_score = (1+catsum) * (1+f["f1"].to_numpy())
mult_score[f['f3'].to_numpy()==1] = -1  # keep the validated distress evict
mult_top = set(np.argpartition(-mult_score, TOP)[:TOP].tolist())
v19_top = set(np.argpartition(-s19, TOP)[:TOP].tolist())
jac = len(mult_top & v19_top)/len(mult_top | v19_top)
print(f"  multiplicative (1+catsum)*(1+f1) top-20% vs v19 top-20%: jaccard={jac:.4f}  overlap%={len(mult_top&v19_top)/TOP:.2%}")
pr_mult = p.proxy(mult_score)
print(f"  multiplicative form proxy = {pr_mult:.4f} vs v19 baseline {p.proxy(s19):.4f}  delta={pr_mult-p.proxy(s19):+.4f}")
