"""H1 probe: does the dropped COST side break boundary ties?

Hypothesis: at the dense top-20% boundary the revenue terms (f7, f1) saturate, so the tie-breaker
is COST — rewards burn (f21) and benefit credits (f13-f16) — which v19 ignores. Test as a tunable
subtraction on v19 and screen via the validated LB-predictor (no submission). Three forms:
  H1a absolute rewards cost   H1b absolute benefit cost   H1c cost-per-$ burden (orthogonal to spend)
Run: .venv/bin/python scratchpad/h1_costside.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA                                    # noqa: E402
from score_magnitude import dollar_profit_v19_lending, spend_dollars, _z, CPP, LOUNGE_COST  # noqa: E402
from lb_predict import LBPredictor, TOP                       # noqa: E402

df = PremierEDA().df
ids = df["id"].to_numpy()
f = df.fillna(0.0)
s19 = dollar_profit_v19_lending(df).to_numpy()
f3 = (f["f3"].to_numpy() == 1)

rewards_cost = CPP * f["f21"].to_numpy()                                      # realized reward $ ($/pt=0.01)
benefit_cost = LOUNGE_COST * f["f13"].to_numpy() + f["f14"].to_numpy() + 15.0 * f["f15"].to_numpy() + f["f16"].to_numpy()
spend = spend_dollars(df).to_numpy()
burden = (rewards_cost + benefit_cost) / (spend + np.median(spend[spend > 0]))  # cost-per-$, stabilized

p = LBPredictor(ids=ids)
base = p.proxy(s19)
print(f"v19 baseline proxy {base:.4f}  predicted-LB {p.predict(s19):.4f}  (actual 0.859)\n")


def screen(name: str, cost_z: np.ndarray):
    print(f"{name}   (subtract w * z(cost), re-apply f3 screen):")
    print(f"{'w':>7}{'proxy':>9}{'pred-LB':>9}{'vs v19':>9}")
    peak = (base, 0.0)
    for w in (0.0, 0.05, 0.10, 0.20, 0.35, 0.50, 0.80):
        sc = s19 - w * cost_z
        sc[f3] = sc.min() - 1.0
        pr = p.proxy(sc)
        tag = "  <==" if pr > base else ""
        print(f"{w:>7.2f}{pr:>9.4f}{p.predict(sc):>9.4f}{pr-base:>+9.4f}{tag}")
        if pr > peak[0]:
            peak = (pr, w)
    print(f"  peak: w={peak[1]:.2f}  +{peak[0]-base:.4f}  "
          f"{'CONFIDENT (>0.02)' if peak[0]-base > 0.020 else 'within noise / no gain'}\n")
    return peak


screen("H1a absolute rewards cost (f21)", _z(rewards_cost))
screen("H1b absolute benefit cost (f13-f16)", _z(benefit_cost))
screen("H1c cost-per-$ burden (orthogonal to spend)", _z(burden))
