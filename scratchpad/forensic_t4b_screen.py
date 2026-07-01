"""Thread 4b: screen the two standout boundary-effect-size derived features via the LB-predictor.
supp_density=catsum/f19 (effsize+0.104) and catsum_x_(1-f11) (effsize+0.137) -- are these orthogonal levers
or just monotone restatements of v19's existing f7/catsum terms? (orthogonality test + proper screen)"""
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
print(f"baseline proxy = {base:.4f}\n")

f = df.fillna(0.0)
catsum = f[SPEND_CATS].sum(axis=1).to_numpy()
f19 = f["f19"].to_numpy(); f11 = f["f11"].to_numpy()

supp_density = catsum / np.maximum(f19, 1)
catsum_risk_adj = catsum * (1 - f11)

print("orthogonality check (Spearman vs v19 and vs catsum directly):")
print(f"  corr(supp_density, v19 score) spearman = {pd.Series(supp_density).corr(pd.Series(s19), method='spearman'):.4f}")
print(f"  corr(supp_density, catsum) spearman = {pd.Series(supp_density).corr(pd.Series(catsum), method='spearman'):.4f}")
print(f"  corr(catsum_risk_adj, v19 score) spearman = {pd.Series(catsum_risk_adj).corr(pd.Series(s19), method='spearman'):.4f}")
print(f"  corr(catsum_risk_adj, catsum) spearman = {pd.Series(catsum_risk_adj).corr(pd.Series(catsum), method='spearman'):.4f}")
print(f"  (if corr-with-catsum is near 1.0, it's the SAME ranking signal v19 already captures via f7/f8/f9/f10 weights, not new info)\n")

sd_score = s19.std()
print("=== A. supp_density as an ADDITIVE boost term ===")
for w in [-0.5, -0.2, -0.1, 0.0, 0.05, 0.1, 0.2, 0.3, 0.5]:
    z = (supp_density - supp_density.mean()) / (supp_density.std() + 1e-9)
    cand = s19 + w * sd_score * z
    cand[df['f3'].fillna(0).to_numpy()==1] = cand.min() - 1
    pr = p.proxy(cand)
    flag = "  <==" if pr > base else ""
    print(f"  w={w:+.2f}: proxy={pr:.4f}  delta={pr-base:+.4f}{flag}")

print("\n=== B. catsum_x_(1-f11) [risk-discounted spend] as a REPLACEMENT for catsum inside v19's spend term ===")
# v19 uses raw f7/f8/f9/f10/f6 weighted; test discounting by (1-f11) globally as a multiplicative factor
risk_discount = (1 - f11)
print(f"  f11 stats: mean={f11.mean():.5f} median={np.median(f11):.5f} max={f11.max():.4f} -> discount factor range [{risk_discount.min():.3f},{risk_discount.max():.3f}]")
for w in [0.0, 0.25, 0.5, 0.75, 1.0]:
    factor = (1 - w * f11)   # partial risk-discount on the WHOLE v19 score
    cand = s19 * factor
    cand[df['f3'].fillna(0).to_numpy()==1] = cand.min() - 1
    pr = p.proxy(cand)
    flag = "  <==" if pr > base else ""
    print(f"  risk-discount w={w:.2f} (multiply whole score by 1-{w}*f11): proxy={pr:.4f}  delta={pr-base:+.4f}{flag}")

print("\n=== C. f19 as a DIVISOR applied to v19's existing score (does normalizing by supp-accounts help?) ===")
for w in [0.0, 0.1, 0.2, 0.3, 0.5, 1.0]:
    norm = s19 / (1 + w*(f19-1))   # w=0 no effect; w=1 full division by f19
    norm[df['f3'].fillna(0).to_numpy()==1] = norm.min() - 1
    pr = p.proxy(norm)
    flag = "  <==" if pr > base else ""
    print(f"  divide-by-(1+{w}*(f19-1)): proxy={pr:.4f}  delta={pr-base:+.4f}{flag}")
