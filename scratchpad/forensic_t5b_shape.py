"""Thread 5b: fix Gini calc + finish distribution-shape diagnostics (skew/concentration/whale-shape)."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
import numpy as np
from scipy import stats as sps

df = PremierEDA().df
s19 = dollar_profit_v19_lending(df).to_numpy()
order = np.argsort(-s19)
TOP = 100_000

print(f"v19 score: skew={sps.skew(s19):.3f}  kurtosis={sps.kurtosis(s19):.3f}")

shifted = s19 - s19.min() + 1e-9
sorted_s = np.sort(shifted)
n = len(sorted_s)
cum = np.cumsum(sorted_s)
lorenz = cum / cum[-1]
gini = 1 - 2*np.sum(lorenz)/n + 1/n
print(f"v19 Gini coefficient (shifted to positive) = {gini:.4f}")

total_mass = shifted.sum()
print(f"\nConcentration nesting (does the TOP of v19's own top-20% dominate the rest of it? whale-check):")
for pct, k in [(0.01, 5000), (0.05, 25000), (0.10, 50000), (0.20, 100000)]:
    seg = shifted[order[:k]]
    share = seg.sum() / total_mass
    print(f"  top-{pct:.0%} ({k} members): score-mass share = {share:.1%}  (proportional baseline {pct:.0%}, ratio {share/pct:.2f}x)")

print(f"\nWithin the top-20% ONLY, how concentrated is the score-mass (whale-within-whale)?")
top20_mass = shifted[order[:TOP]]
top20_total = top20_mass.sum()
for pct, k in [(0.05, 5000), (0.25, 25000), (0.50, 50000)]:
    share = top20_mass[np.argsort(-top20_mass)][:k].sum() / top20_total
    print(f"  top-{pct:.0%}-OF-the-top20% ({k}/{TOP}): mass share={share:.1%}")

print("\n=== for comparison: same Gini/concentration for raw catsum and raw f1 (the two main inputs) ===")
f = df.fillna(0.0)
catsum = f[SPEND_CATS].sum(axis=1).to_numpy()
f1 = f["f1"].to_numpy()
for name, v in [("catsum", catsum), ("f1", f1)]:
    vv = np.sort(v)
    cum2 = np.cumsum(vv)
    lorenz2 = cum2/cum2[-1]
    g = 1 - 2*np.sum(lorenz2)/n + 1/n
    print(f"  {name}: Gini={g:.4f}")
