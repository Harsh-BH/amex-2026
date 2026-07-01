"""Corrected isolation (h3_isolate_weights.py had a no-bd-cohort-treatment bug -- this version uses
f.fillna(0.0) directly on f6-f10, EXACTLY matching v19's own no-breakdown treatment, so the ONLY
variable across these tests is the precise-economics RATES/WEIGHTS, not cohort handling."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA, SPEND_CATS                                            # noqa: E402
from score_magnitude import dollar_profit_v19_lending, _z, LGD, RECOVERED_W_V19, RECOVERED_RISK_W  # noqa: E402
from lb_predict import LBPredictor, TOP                                           # noqa: E402

df = PremierEDA().df
ids = df["id"].to_numpy()
f = df.fillna(0.0)              # <-- EXACTLY v19's own no-bd treatment (f6-f10 -> 0 when missing)
N = len(df)
s19 = dollar_profit_v19_lending(df).to_numpy()
f3 = (f["f3"].to_numpy() == 1)
p = LBPredictor(ids=ids)
base = p.proxy(s19)


def topmask(score):
    m = np.zeros(N, bool); m[np.argpartition(-score, TOP)[:TOP]] = True; return m


def jac(score):
    a, b = topmask(score), topmask(s19); return float((a & b).sum()) / float((a | b).sum())


def apply_f3(score):
    out = score.copy(); out[f3] = out.min() - 1.0; return out


def report(name, score):
    pr = p.proxy(score)
    print(f"{name:<58}{pr:>8.4f}{pr-base:>+9.4f}{jac(score):>9.3f}")
    return pr


REWARD_MULT = {"f6": 5.0, "f7": 1.0, "f8": 1.0, "f9": 5.0, "f10": 1.0}
CPP_POINT = 0.015
cat_sp = {c: f[c].to_numpy() for c in SPEND_CATS}     # raw, EXACTLY v19's basis (no-bd = 0)
net_margin_per_cat = {c: (0.022 - REWARD_MULT[c] * CPP_POINT) * cat_sp[c] for c in SPEND_CATS}
interest = 0.12 * f["f1"].to_numpy()
exp_loss = LGD * f["f11"].to_numpy() * f["f1"].to_numpy()

print(f"v19 baseline proxy {base:.4f}\n")
print(f"{'variant':<58}{'proxy':>8}{'vs v19':>9}{'Jaccard':>9}")
print("-" * 84)

# L (sanity): v19's weights applied to RAW category spend -- must reproduce v19 EXACTLY now
score_L = np.zeros(N)
for c in SPEND_CATS:
    score_L += RECOVERED_W_V19[c] * _z(cat_sp[c])
score_L += RECOVERED_W_V19["f1"] * _z(f["f1"].to_numpy())
score_L += RECOVERED_RISK_W * _z(-exp_loss)
report("L. sanity: v19 weights on raw cat-spend (=v19)", apply_f3(score_L))

# K: v19's RELATIVE weights applied to the SIGN of precise NET MARGIN (negative on travel,
# positive on other) instead of raw spend -- isolates "precise sign" holding weights/scale fixed.
score_K = np.zeros(N)
for c in SPEND_CATS:
    sign = 1.0 if net_margin_per_cat[c].mean() > 0 else -1.0
    score_K += RECOVERED_W_V19[c] * sign * _z(cat_sp[c])     # flip travel categories' contribution sign
score_K += RECOVERED_W_V19["f1"] * _z(f["f1"].to_numpy())
score_K += RECOVERED_RISK_W * _z(-exp_loss)
report("K. v19 weights + PRECISE-ECONOMICS SIGN on travel (f6,f9 neg)", apply_f3(score_K))

# N: v19's category weights, but interest weight replaced literally (z-scored 12%*f1 with v19's
# OWN f1 weight ratio preserved, i.e. just confirming the rate itself doesn't matter since z-scoring
# normalizes scale -- the literal 12% vs 8% only matters if NOT re-z-scored)
score_N = np.zeros(N)
for c in SPEND_CATS:
    score_N += RECOVERED_W_V19[c] * _z(cat_sp[c])
score_N += RECOVERED_W_V19["f1"] * _z(interest)         # z(12%*f1) === z(f1) after z-scoring (scale-invariant)
score_N += RECOVERED_RISK_W * _z(-exp_loss)
report("N. v19 weights, interest=z(12%xf1) [should == L, z-invariant]", apply_f3(score_N))

print("\n=> If K << L, the SIGN (penalize travel) is the dominant failure mode -- holding v19's\n"
      "   calibrated relative weights fixed and changing ONLY the travel sign should reproduce\n"
      "   roughly the v6/v8 LB-loss magnitude (-0.05 to -0.09), confirming sign is the lever\n"
      "   that matters, not the literal dollar RATES (which wash out under z-scoring, see N==L).")
