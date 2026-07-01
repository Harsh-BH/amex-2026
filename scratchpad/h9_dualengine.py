"""BOLD bet: dual-engine interaction. A member who BOTH spends heavily AND carries a revolving balance
is a premium relationship (interchange + interest from the same customer, higher CLV) — reward the
INTERSECTION on top of v22's additive spine. Transactors (f1=0) get interaction=0 -> unaffected (whale-safe).
Overshoot guard: it's an ADD-ON bonus to v22 (not a restructure like v20's lending-dominant), tuned via the
v19->v22 gradient compass. Run: .venv/bin/python scratchpad/h9_dualengine.py
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd

ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS                            # noqa: E402
from score_magnitude import dollar_profit_v19_lending, dollar_profit_v22_hybrid  # noqa: E402
from lb_predict import TOP                                        # noqa: E402

df = PremierEDA().df
f = df.fillna(0.0)
f3 = (f["f3"].to_numpy() == 1)
SMALL = {"f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}
whale = (f["f1"].to_numpy() == 0) & (f["f7"].to_numpy() > np.quantile(f["f7"].to_numpy(), 0.95))


def _zc(v):
    v = np.asarray(v, float); return v / (v.std() + 1e-9)
def _rank(v):
    return pd.Series(np.asarray(v, float)).rank(pct=True).to_numpy()
def topset(s):
    return set(np.argsort(-np.asarray(s))[:TOP])


t19, t22 = topset(dollar_profit_v19_lending(df).to_numpy()), topset(dollar_profit_v22_hybrid(df).to_numpy())
wi = np.where(whale)[0]

catsum = f[list(SPEND_CATS)].sum(axis=1).to_numpy()
spend_r = _rank(catsum)                                           # spend magnitude, 0-1
f1v = f["f1"].to_numpy()
revint = np.where(f1v > 0, _rank(f1v), 0.0)                        # revolving intensity, 0 for transactors
inter = spend_r * revint                                          # high only when BOTH high


def v24(lam):
    sc = 0.738 * _zc(f["f7"].to_numpy()) + 0.738 * _zc(f1v)
    for k, wv in SMALL.items():
        sc = sc + wv * _zc(_rank(f[k].to_numpy()))
    sc = sc + 0.110 * _zc(-(f["f11"].to_numpy() * f1v))
    sc = sc + lam * _zc(inter)                                     # dual-engine bonus
    sc[f3] = sc.min() - 1.0
    return sc


print(f"dual-engine members (spend>p50 & f1>0): {((catsum>np.median(catsum))&(f1v>0)).mean():.1%} of pop")
print(f"{'lam':>6}{'ov22':>7}{'ov19':>7}{'whale':>7}{'distinct':>9}  gradient")
for lam in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.4):
    s = v24(lam); t = topset(s)
    ni, no = np.array(sorted(t - t22)), np.array(sorted(t22 - t))
    cont = ""
    if len(ni) and len(no):
        so = f.loc[no, list(SMALL)].max(axis=1).median(); si = f.loc[ni, list(SMALL)].max(axis=1).median()
        # also: are the promoted members revolvers (dual-engine)? are demoted single-engine?
        pr_rev = (f1v[ni] > 0).mean(); dm_rev = (f1v[no] > 0).mean()
        cont = f"promote-rev% {pr_rev:.0%} vs demote-rev% {dm_rev:.0%}  spike out{so:.0f}/in{si:.0f} {'CONT' if so>si else 'rev'}"
    print(f"{lam:>6.2f}{len(t&t22)/TOP:>7.3f}{len(t&t19)/TOP:>7.3f}{np.mean([i in t for i in wi]):>7.3f}{len(set(np.round(s,6))):>9,}  {cont}")
