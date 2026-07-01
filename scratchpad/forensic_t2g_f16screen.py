"""Screen f16-saturation as a signal: members WHO saturate their entertainment credit (f16>=64) might be
heavier benefit-users / more "engaged" -- test if f16-saturation correlates with value, and if adding it helps."""
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
base = p.proxy(s19)

f16 = df["f16"].to_numpy(float)
saturated = (f16 >= 64.0)  # missing -> False (NaN comparison)
print(f"f16-saturated (>=64): n={np.nansum(saturated)} ({np.nanmean(saturated.astype(float)):.1%} of non-missing, "
      f"{saturated.sum()/len(df):.1%} of population)")

f = df.fillna(0.0)
catsum = f[SPEND_CATS].sum(axis=1).to_numpy()
sat_mask = (df["f16"].fillna(0).to_numpy() >= 64.0)
print(f"saturated catsum mean={catsum[sat_mask].mean():.0f} vs non-sat={catsum[~sat_mask].mean():.0f} "
      f"(pop {catsum.mean():.0f})")
print(f"saturated v19score mean={s19[sat_mask].mean():.3f} vs non-sat={s19[~sat_mask].mean():.3f}")

print("\nscreen as additive term:")
sd = s19.std()
for w in [0.0, 0.05, 0.1, 0.2, 0.3]:
    cand = s19 + w*sd*sat_mask.astype(float)
    cand[df['f3'].fillna(0).to_numpy()==1] = cand.min()-1
    pr = p.proxy(cand)
    flag = "  <==" if pr > base else ""
    print(f"  w={w}: proxy={pr:.4f} delta={pr-base:+.4f}{flag}")

print("\n=== f13=3 ('3+' censored lounge bucket) -- is it correlated with high value, supporting a benefit-loyalty read? ===")
f13 = df["f13"].fillna(0).to_numpy()
for v in [0,1,2,3]:
    m = (f13==v)
    print(f"  f13={v}: n={m.sum()}  mean catsum={catsum[m].mean():.0f}  mean v19score={s19[m].mean():.3f}")
