"""v24 dual-engine WON 0.880 (+0.014). Push the axis. Compass is now the v22->v24 delta (our strongest
confirmed direction). Candidates: (a) higher lambda (more dual-engine reward — climb or overshoot?),
(b) v24 + margin lever (stack three), (c) both. Screen: overlap with v24 (anchor to best), whale-protection
(must hold ~0.999 — dropping whales = losing direction), continues-v22->v24 (promote higher-interaction than
demote). Run: .venv/bin/python scratchpad/h10_push_dualengine.py
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd

ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS                            # noqa: E402
from score_magnitude import dollar_profit_v22_hybrid, dollar_profit_v24_dualengine, V23_MARGIN  # noqa: E402
from lb_predict import TOP                                        # noqa: E402

df = PremierEDA().df
f = df.fillna(0.0)
f3 = (f["f3"].to_numpy() == 1)
SMALL = {"f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}
f1v = f["f1"].to_numpy()
whale = (f1v == 0) & (f["f7"].to_numpy() > np.quantile(f["f7"].to_numpy(), 0.95))
wi = np.where(whale)[0]


def _zc(v):
    v = np.asarray(v, float); return v / (v.std() + 1e-9)
def _rank(v):
    return pd.Series(np.asarray(v, float)).rank(pct=True).to_numpy()
def topset(s):
    return set(np.argsort(-np.asarray(s))[:TOP])


catsum = f[list(SPEND_CATS)].sum(axis=1).to_numpy()
spend_r = _rank(catsum)
revint = np.where(f1v > 0, _rank(f1v), 0.0)
inter = spend_r * revint                                          # the dual-engine interaction


def build(lam, margin_w=0.0):
    sc = 0.738 * _zc(f["f7"].to_numpy()) + 0.738 * _zc(f1v)
    for k, wv in SMALL.items():
        sc = sc + wv * _zc(_rank(f[k].to_numpy()))
    sc = sc + 0.110 * _zc(-(f["f11"].to_numpy() * f1v))
    sc = sc + lam * _zc(inter)
    if margin_w:
        sc = sc + margin_w * _zc(sum(m * f[k].to_numpy() for k, m in V23_MARGIN.items()))
    sc[f3] = sc.min() - 1.0
    return sc


t22 = topset(dollar_profit_v22_hybrid(df).to_numpy())
t24 = topset(dollar_profit_v24_dualengine(df).to_numpy())         # our current best (0.880)
gain_in24 = t24 - t22                                             # v24's winning promotions (dual-engine)
print(f"v22->v24 promoted {len(gain_in24):,} (mean dual-engine-interaction {inter[sorted(gain_in24)].mean():.3f} "
      f"vs pop {inter.mean():.3f}) — that direction gained +0.014")


def rep(name, s):
    t = topset(s)
    ni, no = sorted(t - t24), sorted(t24 - t)
    cont = ""
    if ni and no:
        cont = f"promote-inter {inter[ni].mean():.3f} vs demote {inter[no].mean():.3f} {'CONT' if inter[ni].mean() > inter[no].mean() else 'rev'}"
    print(f"  {name:<20} ov24 {len(t&t24)/TOP:.3f} whale {np.mean([i in t for i in wi]):.3f} "
          f"distinct {len(set(np.round(s,6))):>7,}  {cont}")


print(f"\n{'variant':<22}{'ov24':>9}{'whale':>7}{'distinct':>10}")
rep("v24 (lam0.20, best)", build(0.20))
print("push lambda (more dual-engine reward):")
for lam in (0.25, 0.30, 0.35, 0.45):
    rep(f"lam{lam}", build(lam))
print("stack margin on v24 (three levers):")
for mw in (0.10, 0.15, 0.20):
    rep(f"lam0.20 + margin{mw}", build(0.20, mw))
print("push both:")
rep("lam0.30 + margin0.15", build(0.30, 0.15))
