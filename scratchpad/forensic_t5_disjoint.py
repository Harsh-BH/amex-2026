"""Forensic Thread 5: DISTRIBUTION SHAPE. Is the truth plausibly NOT whale-shaped? Check top-20%-by-
each-single-feature populations, and whether any feature's top-20% is nearly DISJOINT from v19's (signal v19 ignores)."""
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
v19_top = set(np.argpartition(-s19, TOP)[:TOP].tolist())
print(f"baseline proxy={base:.4f}\n")

FEATS = [f"f{i}" for i in range(1, 24)]
f = df.fillna(0.0)
catsum = f[SPEND_CATS].sum(axis=1).to_numpy()

print("=== A. Jaccard overlap of top-20%-by-single-feature vs v19's top-20% ===")
print(f"{'feature':>10}{'jaccard':>10}{'overlap%':>10}")
results = []
for c in FEATS + ["catsum"]:
    v = catsum if c == "catsum" else f[c].to_numpy(float)
    top_c = set(np.argpartition(-v, TOP)[:TOP].tolist())
    inter = len(v19_top & top_c)
    union = len(v19_top | top_c)
    jac = inter/union
    overlap_pct = inter/TOP
    results.append((c, jac, overlap_pct))
results.sort(key=lambda x: x[1])
for c, jac, ov in results:
    flag = "  <-- most DISJOINT" if jac < 0.10 else ""
    print(f"{c:>10}{jac:>10.4f}{ov:>10.2%}{flag}")

print("\n=== B. for each, screen via LB-predictor: does ranking PURELY by that feature beat v19? (sanity floor) ===")
for c in FEATS + ["catsum"]:
    v = catsum if c == "catsum" else f[c].to_numpy(float)
    pr = p.proxy(v)
    flag = "  <== BETTER than v19!" if pr > base else ""
    print(f"  rank-by-{c}: proxy={pr:.4f}  (vs v19 {base:.4f}, delta {pr-base:+.4f}){flag}")

print("\n=== C. distribution shape diagnostics: skew/kurtosis of v19 score + Gini concentration ===")
from scipy import stats as sps
print(f"  v19 score: skew={sps.skew(s19):.3f}  kurtosis={sps.kurtosis(s19):.3f}")
sorted_s = np.sort(s19 - s19.min() + 1e-9)  # shift positive for Gini
cum = np.cumsum(sorted_s)
gini = 1 - 2*np.trapz(cum/cum[-1], dx=1/len(sorted_s))
print(f"  v19 Gini coefficient (shifted positive) = {gini:.4f}")
print(f"  top-20% share of total v19 score-mass (shifted): {(np.sort(s19-s19.min()+1e-9)[::-1][:TOP].sum())/cum[-1]:.1%} (vs 20% if uniform)")

print("\n=== D. is v19 'whale-shaped'? Check concentration WITHIN the top-20% itself (top1%/top5%/top20% nesting) ===")
order = np.argsort(-s19)
for pct, n in [(0.01, 5000), (0.05, 25000), (0.10, 50000), (0.20, 100000)]:
    seg = s19[order[:n]] - s19.min() + 1e-9
    share = seg.sum() / cum[-1]
    print(f"  top-{pct:.0%} ({n}): score-mass share = {share:.1%}  (proportional would be {pct:.0%})")
