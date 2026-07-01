"""Thread 3c: is missingness signature ORTHOGONAL info beyond v19, or just restating what v19 already uses?
v19 uses raw f-values (post fillna(0)), so missingness IS implicitly baked in already (missing->0).
Test: does the missingness-SIGNATURE predict top20 status BEYOND what v19's raw-feature-score already captures?
"""
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
print(f"baseline proxy = {base:.4f}")

miss = df[[f"f{i}" for i in range(1,24)]].isna()

# decode the BEST signature: catspend present, rewards present, lendline MISSING, benefits present, email present/absent mixed
best_sig_mask = (~miss["f6"]) & (~miss["f4"]) & (miss["f17"]) & (~miss["f13"])
print(f"\n'lend-line-missing-only' cohort (has spend+rewards data, NO lend line): n={best_sig_mask.sum()} ({best_sig_mask.mean():.1%})")
sub = df.loc[best_sig_mask]
print(f"  mean f1 (revolve)={sub['f1'].mean():.1f}  mean f5={sub['f5'].mean():.1f}  mean catsum={sub[SPEND_CATS].sum(axis=1).mean():.1f}")
print(f"  mean f4 (rewards)={sub['f4'].mean():.1f}  mean f11 (risk)={sub['f11'].mean():.5f}")
print(f"  -> this is the 'charge-only, high spend/rewards, no revolving debt' segment = TRANSACTOR ELITE")
print(f"  f1==0 rate in this cohort: {(sub['f1']==0).mean():.1%}  (if near-100%, lend-line-missing IS the charge-only flag, already known)")

print("\n=== does adding a missingness-signature DUMMY as an extra additive term move the proxy? ===")
# Build crude per-signature average-rank encoding (like a target-encoded categorical) and test as an ADDITIVE boost.
sig = miss.apply(lambda r: tuple(r[["f4","f6","f17","f13","f22","f23"]].values), axis=1)
sig_rank_score = pd.Series(s19).groupby(sig).transform("mean").to_numpy()  # in-sample target leakage by construction, just a SCREEN for whether signature has residual content
resid = s19 - sig_rank_score  # what's left after removing signature-group-mean
print(f"  variance explained by signature group-means (in v19 score): R2 = {1 - np.var(resid)/np.var(s19):.4f}")
print(f"  -> if R2 is high, signature is REDUNDANT with v19 (v19 already encodes it via fillna(0) zeroing); ")
print(f"     if R2 is low, signature carries info v19 discards")

# direct test: add signature-derived dummy (boolean for the TOP signature) as an extra term, screen via proxy
cand = s19 + 0.3 * s19.std() * best_sig_mask.to_numpy()
cand[df['f3'].fillna(0).to_numpy()==1] = cand.min()-1
pr = p.proxy(cand)
print(f"\n  candidate: v19 + 0.3*sd*best_sig_mask -> proxy={pr:.4f}  delta={pr-base:+.4f}")
for w in [0.1, 0.2, 0.5, 1.0]:
    cand = s19 + w * s19.std() * best_sig_mask.to_numpy()
    cand[df['f3'].fillna(0).to_numpy()==1] = cand.min()-1
    pr = p.proxy(cand)
    print(f"  w={w}: proxy={pr:.4f}  delta={pr-base:+.4f}")
