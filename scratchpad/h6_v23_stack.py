"""v23 = v22 (hybrid basis, LB 0.866) + precise per-$ net-margin term (the A31 blend that scored
+0.018 on the v19 base). Stacks the two independent post-v19 gains. The predictor is blind to v22's
basis, so predict() is NOT informative here — we characterize by Jaccard vs v22 + whale protection.
Run: .venv/bin/python scratchpad/h6_v23_stack.py
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd

ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA                                    # noqa: E402
from score_magnitude import dollar_profit_v22_hybrid         # noqa: E402
from lb_predict import LBPredictor, TOP                       # noqa: E402

df = PremierEDA().df
ids = df["id"].to_numpy()
f = df.fillna(0.0)
f3 = (f["f3"].to_numpy() == 1)


def _zc(v):
    v = np.asarray(v, float)
    return v / (v.std() + 1e-9)


MARGIN = {"f6": -0.053, "f9": -0.053, "f7": 0.007, "f8": 0.007, "f10": 0.007}   # 5x travel vs 1x rest


def v23(w):
    base = dollar_profit_v22_hybrid(df).to_numpy()
    nm = sum(m * f[k].to_numpy() for k, m in MARGIN.items())
    sc = base + w * _zc(nm)
    sc[f3] = sc.min() - 1.0
    return sc


s22 = dollar_profit_v22_hybrid(df).to_numpy()
top22 = set(np.argsort(-s22)[:TOP])
whale = (f["f1"].to_numpy() == 0) & (f["f7"].to_numpy() > np.quantile(f["f7"].to_numpy(), 0.95))
p = LBPredictor(ids=ids)

print(f"v22 base: proxy {p.proxy(s22):.4f} (predictor blind to basis — reference only)")
print(f"{'w':>6}{'Jac vs v22':>12}{'swaps':>8}{'whale-in':>10}{'distinct':>10}{'f3-in-top':>11}")
for w in (0.05, 0.10, 0.15, 0.20, 0.30):
    sc = v23(w)
    topn = set(np.argsort(-sc)[:TOP])
    jac = len(topn & top22) / len(topn | top22)
    wr = np.mean([i in topn for i in np.where(whale)[0]])
    print(f"{w:>6.2f}{jac:>12.3f}{len(topn - top22):>8,}{wr:>10.3f}{len(set(np.round(sc,6))):>10,}{sum(f3[i] for i in topn):>11}")
