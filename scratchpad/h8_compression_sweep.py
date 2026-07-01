"""v22 compressed specialty spend to RANK (p=1) and won. The gradient compass says compressing MORE
(rank^p, p<1) continues the winning direction. Find the sweet spot p, test pure participation (spent-at-all),
and test stacking the precise-margin lever on the best. Compass = ov22>ov19 + whale~0.999 + non-degenerate +
'CONTINUES v22' (demotes bigger specialty-spikers than it promotes). Run: .venv/bin/python scratchpad/h8_compression_sweep.py
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd

ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA                                          # noqa: E402
from score_magnitude import dollar_profit_v19_lending, dollar_profit_v22_hybrid  # noqa: E402
from lb_predict import TOP                                         # noqa: E402

df = PremierEDA().df
f = df.fillna(0.0)
f3 = (f["f3"].to_numpy() == 1)
SMALL = {"f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}
whale = (f["f1"].to_numpy() == 0) & (f["f7"].to_numpy() > np.quantile(f["f7"].to_numpy(), 0.95))
MARGIN = {"f6": -0.053, "f9": -0.053, "f7": 0.007, "f8": 0.007, "f10": 0.007}


def _zc(v):
    v = np.asarray(v, float); return v / (v.std() + 1e-9)
def _rank(v):
    return pd.Series(np.asarray(v, float)).rank(pct=True).to_numpy()
def topset(s):
    return set(np.argsort(-np.asarray(s))[:TOP])


t19, t22 = topset(dollar_profit_v19_lending(df).to_numpy()), topset(dollar_profit_v22_hybrid(df).to_numpy())
wi = np.where(whale)[0]


def build(small_tf, w_margin=0.0):
    sc = 0.738 * _zc(f["f7"].to_numpy()) + 0.738 * _zc(f["f1"].to_numpy())
    for k, wv in SMALL.items():
        sc = sc + wv * _zc(small_tf(f[k].to_numpy()))
    sc = sc + 0.110 * _zc(-(f["f11"].to_numpy() * f["f1"].to_numpy()))
    if w_margin:
        sc = sc + w_margin * _zc(sum(m * f[k].to_numpy() for k, m in MARGIN.items()))
    sc[f3] = sc.min() - 1.0
    return sc


def report(name, s):
    t = topset(s)
    new_in, new_out = t - t22, t22 - t
    cont = ""
    if new_in and new_out:
        so = f.loc[sorted(new_out), list(SMALL)].max(axis=1).median()
        si = f.loc[sorted(new_in), list(SMALL)].max(axis=1).median()
        cont = f"demote-spike {so:>6.0f} vs promote {si:>6.0f} {'CONTINUES' if so > si else 'reverts'}"
    print(f"  {name:<20} ov22 {len(t&t22)/TOP:.3f} ov19 {len(t&t19)/TOP:.3f} whale {np.mean([i in t for i in wi]):.3f} "
          f"distinct {len(set(np.round(s,6))):>7,}  {cont}")


print("rank^p specialty compression (p=1 is v22; p<1 compresses spikes MORE toward participation):")
for p in (1.0, 0.7, 0.5, 0.35, 0.25, 0.15):
    report(f"rank^{p}", build(lambda v, p=p: _rank(v) ** p))
print("\npure participation & count-of-categories (specialty magnitude ignored entirely):")
report("spent-at-all (0/1)", build(lambda v: (v > 0).astype(float)))
print("\nstack precise-margin on the compass-best compression (rank^0.35):")
for wm in (0.0, 0.10, 0.15, 0.20):
    report(f"rank^0.35 + m{wm}", build(lambda v: _rank(v) ** 0.35, w_margin=wm))
