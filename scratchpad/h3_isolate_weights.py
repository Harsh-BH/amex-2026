"""Final isolation: is the -0.41 to -0.23 gap explained by EQUAL term-weights (1:1:1:1:1) vs
v19's CALIBRATED relative weights (f1 z'd at 0.738, f7 at 0.738, f8 0.348, f10/f6/f9 0.060-0.137)?
Test: take the precise-economics REVENUE terms (interchange split by category mirroring v19's
per-category structure + 12% interest) but apply v19's RELATIVE weight ratios to each piece,
keeping the precise DOLLAR units's z-scored magnitudes (so only the weight RATIOS, not the
underlying economics, change). This tells us whether 'exact economics' is wrong on RATES or on
RELATIVE IMPORTANCE.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA, SPEND_CATS                                            # noqa: E402
from score_magnitude import dollar_profit_v19_lending, spend_dollars, _z, LGD, LOUNGE_COST, RECOVERED_W_V19, RECOVERED_RISK_W  # noqa: E402
from lb_predict import LBPredictor, TOP                                           # noqa: E402

df = PremierEDA().df
ids = df["id"].to_numpy()
f = df.fillna(0.0)
N = len(df)
s19 = dollar_profit_v19_lending(df).to_numpy()
f3 = (f["f3"].to_numpy() == 1)
has_bd = df[SPEND_CATS].notna().any(axis=1).to_numpy()
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
    print(f"{name:<56}{pr:>8.4f}{pr-base:>+9.4f}{jac(score):>9.3f}")
    return pr


print(f"v19 baseline proxy {base:.4f}\n")
print("v19's actual weights:", RECOVERED_W_V19, "risk_w", RECOVERED_RISK_W)
print(f"{'variant':<56}{'proxy':>8}{'vs v19':>9}{'Jaccard':>9}")
print("-" * 82)

REWARD_MULT = {"f6": 5.0, "f7": 1.0, "f8": 1.0, "f9": 5.0, "f10": 1.0}
CPP_POINT = 0.015
sp_total = spend_dollars(df).to_numpy()
cat_raw = {c: np.clip(f[c].to_numpy(), -np.inf, None) for c in SPEND_CATS}
bd_sum = sum(np.clip(cat_raw[c][has_bd], 0.0, None) for c in SPEND_CATS).sum()
cat_share = {c: np.clip(cat_raw[c][has_bd], 0.0, None).sum() / bd_sum for c in SPEND_CATS}
cat_sp = {}
for c in SPEND_CATS:
    v = cat_raw[c].copy(); v[~has_bd] = cat_share[c] * sp_total[~has_bd]; cat_sp[c] = v

# precise per-category NET MARGIN (interchange rate - reward rate), all-positive (other categories)
# but travel categories given v19's tested weight RATIOS instead of equal-weight.
net_margin_per_cat = {c: (0.022 - REWARD_MULT[c] * CPP_POINT) * cat_sp[c] for c in SPEND_CATS}
# this nets to: f7/f8/f10 positive ~0.007/$ ; f6/f9 negative ~ -0.053/$

interest = 0.12 * f["f1"].to_numpy()
exp_loss = LGD * f["f11"].to_numpy() * f["f1"].to_numpy()

# K: precise-rate-derived but apply v19's EXACT relative weight structure: z-score each category
# margin term THEN weight by v19's actual recovered ratios (so the underlying $-rate economics
# determine SIGN+RELATIVE-WITHIN-CAT-SCALE, but cross-term importance = v19's calibrated weights).
score_K = np.zeros(N)
for c in SPEND_CATS:
    score_K += RECOVERED_W_V19[c] * _z(net_margin_per_cat[c]) * np.sign(net_margin_per_cat[c].mean() + 1e-12)
score_K += RECOVERED_W_V19["f1"] * _z(interest)
score_K += RECOVERED_RISK_W * _z(-exp_loss)
report("K. precise signs + v19 RELATIVE weights (travel sign as-is)", apply_f3(score_K))

# L: same but force travel categories' sign to POSITIVE (matching v19's actual all-positive bet)
# i.e. apply v19's weights directly to RAW category $ (ignore the negative-margin direction),
# which is EXACTLY v19 itself by construction -- sanity check this reproduces v19 ~exactly
score_L = np.zeros(N)
for c in SPEND_CATS:
    score_L += RECOVERED_W_V19[c] * _z(cat_sp[c])
score_L += RECOVERED_W_V19["f1"] * _z(f["f1"].to_numpy())
score_L += RECOVERED_RISK_W * _z(-(f["f11"].to_numpy() * f["f1"].to_numpy()))
report("L. v19 weights on raw cat-spend (sanity: should ~= v19)", apply_f3(score_L))
print(f"   Jaccard(L, actual v19 fn) = {jac(dollar_profit_v19_lending(df).to_numpy()):.3f} <- should be 1.000 if L is byte-identical-ish")
real_v19 = dollar_profit_v19_lending(df).to_numpy()
a, b = topmask(score_L), topmask(real_v19)
print(f"   Jaccard(L vs actual v19 fn) = {(a&b).sum()/(a|b).sum():.4f}")

# M: precise economics REVENUE side using v19's weight RATIOS, but interest weight EXACT 12% scaled
# (not v19's recalibrated co-equal bet) -- isolate "use brief's literal 12%" vs "v19's tuned f1 weight"
print()
print("--- isolating: does the LITERAL 12% rate (vs v19's tuned 0.738 f1 weight) matter on its own? ---")
score_M = np.zeros(N)
for c in SPEND_CATS:
    score_M += RECOVERED_W_V19[c] * _z(cat_sp[c])
score_M += _z(interest)   # interest UNWEIGHTED-relative (just z-scored 12%xf1, no v19 ratio applied)
score_M += RECOVERED_RISK_W * _z(-exp_loss)
report("M. v19 spend weights + UNSCALED z(12%*f1) interest", apply_f3(score_M))
