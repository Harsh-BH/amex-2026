"""H2 probe: two-population (revolver vs transactor) merge calibration.

v19 already merges segments via the global f1 z-score (a FIXED implicit merge). H2 asks:
does the TRUTH want a different transactor/revolver MIX at the top-20% boundary than v19 gives?
We test the cross-segment merge as a tunable knob and screen each setting via the validated
LB-predictor (no submission).  Run: .venv/bin/python scratchpad/h2_segment.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA, SPEND_CATS                       # noqa: E402
from score_magnitude import dollar_profit_v19_lending, _z, RECOVERED_RISK_W  # noqa: E402
from lb_predict import LBPredictor, TOP                       # noqa: E402

df = PremierEDA().df
ids = df["id"].to_numpy()
rev = (df["f1"].to_numpy(float) > 0)                          # revolver: carries a balance (f1 missing=0)
print(f"segments: revolver(f1>0) {rev.mean():.1%}  transactor(f1==0) {(~rev).mean():.1%}")

s19 = dollar_profit_v19_lending(df).to_numpy()
order = np.argsort(-s19)
top = order[:TOP]
band = order[90_000:110_000]                                 # the dense in/out boundary
print(f"v19 top-20%  revolver share {rev[top].mean():.1%}")
print(f"v19 90-110k boundary band  revolver share {rev[band].mean():.1%}  "
      f"(in-band-in {rev[order[90_000:100_000]].mean():.1%} vs out {rev[order[100_000:110_000]].mean():.1%})")

p = LBPredictor(ids=ids)
base_proxy = p.proxy(s19)
base_pred = p.predict(s19)
print(f"\nv19 baseline: proxy {base_proxy:.4f}  predicted-LB {base_pred:.4f}  (actual 0.859)")
sd = s19.std()

# ---- H2a: flat segment-mix offset. final = v19 + delta*(revolver). Shifts the segment boundary
# without reordering within-segment. delta>0 => more revolvers in top-20%; <0 => more transactors. ----
print("\nH2a  cross-segment offset  (delta in units of v19-score std):")
print(f"{'delta':>7}{'rev share top':>15}{'proxy':>9}{'pred-LB':>9}{'vs v19':>9}")
best = (base_proxy, 0.0, "v19")
for c in (-0.40, -0.25, -0.15, -0.08, 0.0, 0.08, 0.15, 0.25, 0.40):
    sc = s19 + c * sd * rev
    pr = p.proxy(sc)
    flag = "  <== " + ("better" if pr > base_proxy + 0.0 else "") if pr > base_proxy else ""
    print(f"{c:>7.2f}{rev[np.argsort(-sc)[:TOP]].mean():>14.1%}{pr:>9.4f}{p.predict(sc):>9.4f}{pr-base_proxy:>+9.4f}{flag}")
    if pr > best[0]:
        best = (pr, c, f"H2a delta={c:+.2f}")

# ---- H2b: true two-model — standardize spend WITHIN each segment, score each by its own P&L,
# merge with a tunable segment location theta. Tests "measure each member against their own peers". ----
def h2b(theta: float) -> np.ndarray:
    f = df.fillna(0.0)
    W = {"f7": 0.738, "f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}
    sc = np.zeros(len(df))
    for seg in (rev, ~rev):
        spend = np.zeros(int(seg.sum()))
        for k, wv in W.items():
            spend += wv * _z(f[k].to_numpy()[seg])
        sc[seg] = spend
    # revolver-only engines (interest + expected loss), standardized within revolvers
    sc[rev] += 0.738 * _z(f["f1"].to_numpy()[rev])
    expl = -(f["f11"].to_numpy()[rev] * f["f1"].to_numpy()[rev])
    sc[rev] += RECOVERED_RISK_W * _z(expl)
    sc += theta * rev                                         # merge location
    sc[f["f3"].to_numpy() == 1] = sc.min() - 1.0             # keep the validated distress screen
    return sc

print("\nH2b  two-model within-segment z + merge location theta:")
print(f"{'theta':>7}{'rev share top':>15}{'proxy':>9}{'pred-LB':>9}{'vs v19':>9}")
for th in (-0.5, 0.0, 0.5, 1.0, 1.5, 2.0):
    sc = h2b(th)
    pr = p.proxy(sc)
    print(f"{th:>7.2f}{rev[np.argsort(-sc)[:TOP]].mean():>14.1%}{pr:>9.4f}{p.predict(sc):>9.4f}{pr-base_proxy:>+9.4f}")
    if pr > best[0]:
        best = (pr, th, f"H2b theta={th:+.2f}")

print(f"\nBEST: {best[2]}  proxy {best[0]:.4f}  (v19 {base_proxy:.4f}, +{best[0]-base_proxy:.4f}; "
      f"noise floor 0.020 -> {'CONFIDENT' if best[0]-base_proxy > 0.020 else 'within noise, NOT a confident win'})")
