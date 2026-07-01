"""H5: the one genuinely-untested lever from the fresh sweep = a BASIS TRANSFORM.

Two submit-ready candidates built on the v19 spine, both keeping the f3 distress screen:
  (A) HYBRID-BASIS  — keep f7 & f1 on the dollar/std basis (linear-in-$ revenue, PROTECTS the
      consensus-core whales), but RANK-normalize the small specialty cats f6/f8/f9/f10 (where
      std-scaling lets a moderate specialty spender masquerade as a whale). lb_predict is BLIND
      to this (basis change) -> it can't screen it; this needs a real submission.
  (B) PRECISE-MARGIN BLEND — v19 + w*z(precise per-$ net margin from brief slide-8 economics).
      lb_predict CAN see this; agent-2 found it peaks +0.013..0.018 (sub-noise but predictor
      under-predicts the frontier by ~0.035, so it may be a real small gain).

Validate: deterministic, 0 NaN, f3 evicted from top-20%, and CRUCIALLY confirm the hybrid does
NOT demote the f7-whales (the 0.97-1.00-in-rate consensus core = the LB-rejected direction).
Run: .venv/bin/python scratchpad/h5_hybrid_basis.py
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd

ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA                                    # noqa: E402
from score_magnitude import dollar_profit_v19_lending        # noqa: E402
from lb_predict import LBPredictor, TOP                       # noqa: E402

df = PremierEDA().df
ids = df["id"].to_numpy()
f = df.fillna(0.0)
f3 = (f["f3"].to_numpy() == 1)


def _zc(v):                                                   # v19's basis: scale by std, no centering
    v = np.asarray(v, float)
    return v / (v.std() + 1e-9)


def hybrid_basis(df, w_f1=0.738):
    dollar = {"f7": 0.738, "f1": w_f1}                        # raw $ basis — protects whales
    rankcats = {"f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}   # rank-normalized
    score = np.zeros(len(df))
    for k, wv in dollar.items():
        score += wv * _zc(f[k].to_numpy())
    for k, wv in rankcats.items():
        pct = pd.Series(f[k].to_numpy()).rank(pct=True).to_numpy()     # percentile in [0,1]
        score += wv * _zc(pct)
    expl = -(f["f11"].to_numpy() * f["f1"].to_numpy())
    score += 0.110 * _zc(expl)
    s = pd.Series(score, index=df.index)
    return s.mask(pd.Series(f3, index=df.index), s.min() - 1.0)


# precise per-$ net margin (brief slide 8): interchange 2.2% - reward (5x travel / 1x rest)*1.5c/pt
MARGIN = {"f6": -0.053, "f9": -0.053, "f7": 0.007, "f8": 0.007, "f10": 0.007}   # 5x:0.022-0.075; 1x:0.022-0.015


def margin_blend(df, w):
    s19 = dollar_profit_v19_lending(df).to_numpy()
    nm = sum(m * f[k].to_numpy() for k, m in MARGIN.items())
    sc = s19 + w * _zc(nm)
    sc[f3] = sc.min() - 1.0
    return sc


# ---- validate + characterize ----
s19 = dollar_profit_v19_lending(df).to_numpy()
top19 = set(np.argsort(-s19)[:TOP])
p = LBPredictor(ids=ids)
base = p.proxy(s19)

# the f7-whales the critic flagged: pure transactors (f1==0) with f7 > 95th pct = the consensus core
whale = (f["f1"].to_numpy() == 0) & (f["f7"].to_numpy() > np.quantile(f["f7"].to_numpy(), 0.95))
print(f"v19 baseline proxy {base:.4f}; f7-whales n={whale.sum():,}, v19 in-rate {np.mean([i in top19 for i in np.where(whale)[0]]):.3f}\n")

print("=== (A) HYBRID-BASIS (predictor is BLIND — proxy is NOT informative here) ===")
hb = hybrid_basis(df)
assert hybrid_basis(df).equals(hybrid_basis(df)), "hybrid not deterministic"
assert hb.notna().all(), "hybrid has NaN"
toph = set(np.argsort(-hb.to_numpy())[:TOP])
jac = len(toph & top19) / len(toph | top19)
whale_in = np.mean([i in toph for i in np.where(whale)[0]])
print(f"  deterministic ✓  NaN 0  f3 in top-20%: {sum(f3[i] for i in toph)}")
print(f"  Jaccard vs v19 {jac:.3f}  (swaps {len(toph - top19):,} boundary members)")
print(f"  f7-whale in-rate {whale_in:.3f}  ({'PROTECTED ✓ — avoids the LB-rejected direction' if whale_in > 0.95 else 'DEMOTED ✗ — this is the v6/v8 losing direction, RECONSIDER'})")
print(f"  predict (uninformative, predictor blind to basis): {p.predict(hb):.3f}\n")

print("=== (B) PRECISE-MARGIN BLEND (predictor CAN see this) ===")
for w in (0.08, 0.10, 0.12, 0.15, 0.20):
    sc = margin_blend(df, w)
    pr = p.proxy(sc)
    print(f"  w={w:.2f}  proxy {pr:.4f}  predict {p.predict(sc):.4f}  delta {pr-base:+.4f}")
bw = 0.12
sc = margin_blend(df, bw)
topb = set(np.argsort(-sc)[:TOP])
print(f"  at w={bw}: Jaccard vs v19 {len(topb & top19)/len(topb | top19):.3f}, f3 in top-20% {sum(f3[i] for i in topb)}, "
      f"f7-whale in-rate {np.mean([i in topb for i in np.where(whale)[0]]):.3f}")
