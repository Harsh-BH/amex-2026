"""BOLD interpretable bet: MULTIPLICATIVE dual-engine. v24's additive bonus won +0.014; the stronger
economic claim is that a revolver's SPEND is worth multiplicatively more (interchange + interest compound
in one relationship). score = spend_component x (1 + lam*revolving_intensity) + additive f1 + risk.
Transactors have revint=0 -> factor 1 -> scored on spend alone (whale-safe). Screen vs the v24 anchor +
the v22->v24 winning-direction compass. Also test aggressive-additive v24 (higher lam) for comparison.
Run: .venv/bin/python scratchpad/h11_bold_mult.py
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd

ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS                            # noqa: E402
from score_magnitude import dollar_profit_v22_hybrid, dollar_profit_v24_dualengine  # noqa: E402
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
inter = spend_r * revint


def spend_component():
    s = 0.738 * _zc(f["f7"].to_numpy())
    for k, wv in SMALL.items():
        s = s + wv * _zc(_rank(f[k].to_numpy()))
    return s


def mult(lam):
    S = spend_component(); S = S - S.min() + 0.1                  # shift positive for the multiplier
    sc = S * (1.0 + lam * revint) + 0.738 * _zc(f1v) + 0.110 * _zc(-(f["f11"].to_numpy() * f1v))
    sc[f3] = sc.min() - 1.0
    return sc


def add(lam):                                                    # v24-style additive, tunable lam
    sc = spend_component() + 0.738 * _zc(f1v) + 0.110 * _zc(-(f["f11"].to_numpy() * f1v)) + lam * _zc(inter)
    sc[f3] = sc.min() - 1.0
    return sc


t22, t24 = topset(dollar_profit_v22_hybrid(df).to_numpy()), topset(dollar_profit_v24_dualengine(df).to_numpy())
gin = sorted(t24 - t22)  # v24's winning promotions (dual-engine)
print(f"anchor: v24 (0.880). v22->v24 winning promotions had mean interaction {inter[gin].mean():.3f} vs pop {inter.mean():.3f}")


def rep(name, s):
    t = topset(s)
    ni, no = sorted(t - t24), sorted(t24 - t)
    cont = ""
    if ni and no:
        cont = f"promote-inter {inter[ni].mean():.3f} vs demote {inter[no].mean():.3f} {'CONT' if inter[ni].mean() > inter[no].mean() else 'REV'}"
    print(f"  {name:<18} ov24 {len(t&t24)/TOP:.3f} whale {np.mean([i in t for i in wi]):.3f} moves {len(t-t24):>6,} distinct {len(set(np.round(s,6))):>7,}  {cont}")


print(f"\nMULTIPLICATIVE dual-engine (spend x (1+lam*revint)):")
for lam in (0.5, 1.0, 1.5, 2.0, 3.0):
    rep(f"mult lam{lam}", mult(lam))
print(f"\nAGGRESSIVE ADDITIVE (v24 with higher lam; v24=0.20):")
for lam in (0.30, 0.45, 0.60):
    rep(f"add lam{lam}", add(lam))
