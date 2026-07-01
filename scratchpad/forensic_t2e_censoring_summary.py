"""Catalog ALL censoring/cap evidence across f1-f23 systematically -- the recurring pattern."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA
import numpy as np
import pandas as pd
df = PremierEDA().df

print("=== systematic top-bin-mass-concentration scan (a proxy for 'is this feature censored at its max?') ===")
FEATS = [f"f{i}" for i in range(1,24)]
for c in FEATS:
    v = df[c].dropna()
    if len(v) == 0 or v.max() == v.min(): continue
    vmax = v.max()
    near_max = (v >= vmax*0.995).mean()
    # compare to what we'd expect from a smooth right-tail (use 2nd-highest bin as reference density)
    bins = np.linspace(v.min(), vmax, 21)
    hist, _ = np.histogram(v, bins=bins)
    if len(hist) >= 2 and hist[-2] > 0:
        spike_ratio = hist[-1] / hist[-2]
    else:
        spike_ratio = float('nan')
    flag = "  <-- CENSORED/CAPPED" if near_max > 0.02 and spike_ratio > 2 else ""
    print(f"  {c}: max={vmax:.2f}  mass within 0.5% of max={near_max:.2%}  last-bin/2nd-last-bin ratio={spike_ratio:.2f}{flag}")
