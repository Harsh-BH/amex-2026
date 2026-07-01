"""Forensic Thread 3: MISSINGNESS-PATTERN CLUSTERS. Enumerate distinct missingness "signatures"
across all f1-f23, size each, and check if they correspond to natural segments with different profiles.
"""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
import numpy as np
import pandas as pd

df = PremierEDA().df
FEATS = [f"f{i}" for i in range(1, 24)]
miss = df[FEATS].isna()

print("=== A. per-feature missing rate (sanity vs feature-notes) ===")
for c in FEATS:
    print(f"  {c}: {miss[c].mean():.2%}")

print("\n=== B. distinct missingness signatures (binary vector across 23 features) ===")
sig = miss.apply(lambda r: tuple(r.values), axis=1)
sig_counts = sig.value_counts()
print(f"  total distinct signatures: {len(sig_counts)}")
print(f"  top 25 signatures by size:")
total = len(df)
cum = 0
for i, (s, cnt) in enumerate(sig_counts.head(25).items()):
    cum += cnt
    missing_feats = [FEATS[j] for j, v in enumerate(s) if v]
    print(f"  #{i+1}: n={cnt} ({cnt/total:.2%}, cum {cum/total:.1%})  missing={missing_feats if missing_feats else 'NONE (fully complete)'}")

