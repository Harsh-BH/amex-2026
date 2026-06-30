"""Decompose what the re-triangulated recovered form (with v11min+v15 anchors) actually does
vs v15, and isolate WHICH recovered ingredient (negative travel signs vs spend_log concavity)
drives the divergence. No submission; pure diagnostic."""
import numpy as np, pandas as pd
from pathlib import Path
import sys; sys.path.insert(0, "src")
from eda import PremierEDA, SPEND_CATS

N, TOPK = 500_000, 100_000
df = PremierEDA().df.sort_values("id").reset_index(drop=True)
f = df.fillna(0.0)

def z(v):
    v = np.asarray(v, float); return v / (v.std() + 1e-9)

catsum = df[SPEND_CATS].sum(axis=1, min_count=1).fillna(0.0).to_numpy()
spend_log = np.log1p(np.clip(catsum, 0.0, None))
terms_retri = {
    "f7_other": (0.675, z(f.f7)), "spend_log": (0.420, z(spend_log)),
    "f1_balance": (0.381, z(f.f1)), "f3_delinq": (0.306, z(-f.f3)),
    "f6_airline": (-0.275, z(f.f6)), "f9_lodge": (-0.167, z(f.f9)),
    "benefits": (-0.092, z(-(f.f13+f.f14+f.f15+f.f16))), "f8_ent": (0.084, z(f.f8)),
    "f10_dine": (0.078, z(f.f10)),
}
score_retri = sum(w*v for w, v in terms_retri.values())

W15 = {"f7": 0.738, "f1": 0.523, "f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}
s15 = np.zeros(N)
for k, wv in W15.items():
    s15 += wv * z(f[k])
expl = -(f.f11.values * f.f1.values); s15 += 0.110 * z(expl)
f3 = (f.f3.values == 1); s15 = np.where(f3, s15.min()-1.0, s15)

def top(s):
    return set(np.argpartition(-np.asarray(s), TOPK)[:TOPK])
def jac(a, b):
    A, B = top(a), top(b); return len(A & B)/len(A | B)

terms_v1 = dict(terms_retri)
terms_v1["f6_airline"] = (0.060, z(f.f6)); terms_v1["f9_lodge"] = (0.060, z(f.f9))
score_pos = sum(w*v for w, v in terms_v1.values())

terms_v2 = {k: v for k, v in terms_retri.items() if k != "spend_log"}
score_nolog = sum(w*v for w, v in terms_v2.values())

terms_v3 = {k: v for k, v in terms_retri.items() if k != "spend_log"}
terms_v3["f6_airline"] = (0.060, z(f.f6)); terms_v3["f9_lodge"] = (0.060, z(f.f9))
score_v3 = sum(w*v for w, v in terms_v3.values())

print("Jaccard vs v15 (what drives the divergence?):")
print(f"  retri (full recovered, neg travel + spend_log): {jac(score_retri, s15):.3f}")
print(f"  retri but travel POSITIVE (keep spend_log):      {jac(score_pos, s15):.3f}")
print(f"  retri but DROP spend_log (keep neg travel):      {jac(score_nolog, s15):.3f}")
print(f"  retri travel-pos AND no spend_log:               {jac(score_v3, s15):.3f}")

r_retri = pd.Series(-score_retri).rank()
r15 = pd.Series(-s15).rank()
moved_out = (r15 <= TOPK) & (r_retri > TOPK)
moved_in = (r15 > TOPK) & (r_retri <= TOPK)
print(f"\nv15->retri movers: {moved_out.sum():,} demoted, {moved_in.sum():,} promoted")
travelshare = (f.f6.values + f.f9.values) / (catsum + 1.0)
print(f"  median catsum demoted: {pd.Series(catsum)[moved_out].median():.0f}  promoted: {pd.Series(catsum)[moved_in].median():.0f}")
print(f"  median travel-share demoted: {pd.Series(travelshare)[moved_out].median():.3f}  promoted: {pd.Series(travelshare)[moved_in].median():.3f}")
print(f"  median spend_log demoted: {pd.Series(spend_log)[moved_out].median():.2f}  promoted: {pd.Series(spend_log)[moved_in].median():.2f}")
print(f"  median f1 demoted: {df.loc[moved_out,'f1'].fillna(0).median():.0f}  promoted: {df.loc[moved_in,'f1'].fillna(0).median():.0f}")
