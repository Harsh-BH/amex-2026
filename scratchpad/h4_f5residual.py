"""H4 probe: does f5 carry a WALLET-BREADTH signal beyond the category breakdown?

f5 (total spend, capped ~13.6K) is NOT the sum of f6-f10 (different scale), so we never used it
(r=0.009 with value, ALONE). H4: the RESIDUAL of f5 after regressing out the categories = spend
the named categories DON'T capture = a possible off-category / wallet-breadth signal. Add the
orthogonal residual to v19, sweep the weight both signs, screen via the validated LB-predictor.
Controls: raw f5, and off-category SHARE.  Run: .venv/bin/python scratchpad/h4_f5residual.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA, SPEND_CATS                        # noqa: E402
from score_magnitude import dollar_profit_v19_lending, spend_dollars, _z  # noqa: E402
from lb_predict import LBPredictor, TOP                       # noqa: E402

df = PremierEDA().df
ids = df["id"].to_numpy()
f3 = (df["f3"].fillna(0).to_numpy() == 1)
s19 = dollar_profit_v19_lending(df).to_numpy()

f5 = df["f5"].to_numpy(float)
cats = df[SPEND_CATS].to_numpy(float)                          # f6..f10
has_bd = np.isfinite(cats).any(axis=1)
fit = has_bd & np.isfinite(f5)                                 # rows with BOTH f5 and a breakdown
C = np.nan_to_num(cats)                                        # zero the few intra-row NaNs for the fit

# OLS: f5 ~ [1, f6..f10] on the fit cohort; residual = part of f5 the categories can't explain
A = np.column_stack([np.ones(fit.sum()), C[fit]])
coef, *_ = np.linalg.lstsq(A, f5[fit], rcond=None)
pred_full = coef[0] + C @ coef[1:]
resid = np.where(fit, f5 - pred_full, 0.0)                     # 0 where undefined (no-bd or f5 missing)
r2 = 1 - np.var(f5[fit] - pred_full[fit]) / np.var(f5[fit])
print(f"OLS f5~categories on {fit.sum():,} rows: R^2={r2:.3f}  "
      f"residual std {resid[fit].std():.0f}  corr(resid, v19)={np.corrcoef(resid[fit], s19[fit])[0,1]:+.3f}")

# off-category SHARE control: how much of quantile-matched total spend is NOT in the categories
sp = spend_dollars(df).to_numpy()
off_share = np.where(fit, resid / (np.abs(f5) + np.median(f5[fit])), 0.0)

p = LBPredictor(ids=ids)
base = p.proxy(s19)
print(f"\nv19 baseline proxy {base:.4f}  predicted-LB {p.predict(s19):.4f}  (actual 0.859)\n")


def screen(name: str, term: np.ndarray):
    tz = _z(term)
    print(f"{name}:")
    print(f"{'w':>7}{'proxy':>9}{'pred-LB':>9}{'vs v19':>9}")
    peak = (base, 0.0)
    for w in (-0.40, -0.20, -0.10, -0.05, 0.0, 0.05, 0.10, 0.20, 0.40):
        sc = s19 + w * tz
        sc[f3] = sc.min() - 1.0
        pr = p.proxy(sc)
        tag = "  <==" if pr > base else ""
        print(f"{w:>7.2f}{pr:>9.4f}{p.predict(sc):>9.4f}{pr-base:>+9.4f}{tag}")
        if pr > peak[0]:
            peak = (pr, w)
    verdict = "CONFIDENT (>0.02)" if peak[0]-base > 0.020 else "within noise / no gain"
    print(f"  peak: w={peak[1]:+.2f}  +{peak[0]-base:.4f}  {verdict}\n")


screen("H4a  f5 residual (orthogonal to categories)", resid)
screen("H4b  raw f5 (control — known r=0.009 alone)", np.nan_to_num(f5))
screen("H4c  off-category share (resid / f5)", off_share)
