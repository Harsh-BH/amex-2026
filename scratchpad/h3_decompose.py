"""H3 follow-up: decompose WHY the pure $ P&L (variant 1) is so much worse (-0.41) than prior
margin-sign tests (v6 -0.058, v8 -0.087). Is it (a) the travel-penalty sign, (b) the RAW-DOLLAR
SCALE (no z-scoring -> total spend magnitude swamps everything, same failure as v3-v7 raw-dollar
family which capped 0.614-0.768), or (c) the 12%-flat-interest-revenue swamping balance the same way?
Isolate each by testing an ALL-POSITIVE precise-economics P&L (no travel penalty) on the SAME raw-$
scale, and also a z-scored version of the precise economics (apples-to-apples with v19's basis).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA, SPEND_CATS                                            # noqa: E402
from score_magnitude import dollar_profit_v19_lending, spend_dollars, _z, LGD, LOUNGE_COST  # noqa: E402
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
    print(f"{name:<48}{pr:>8.4f}{pr-base:>+9.4f}{jac(score):>9.3f}")
    return pr


REWARD_MULT = {"f6": 5.0, "f7": 1.0, "f8": 1.0, "f9": 5.0, "f10": 1.0}
CPP_POINT = 0.015
sp_total = spend_dollars(df).to_numpy()
cat_raw = {c: np.clip(f[c].to_numpy(), -np.inf, None) for c in SPEND_CATS}
bd_sum = sum(np.clip(cat_raw[c][has_bd], 0.0, None) for c in SPEND_CATS).sum()
cat_share = {c: np.clip(cat_raw[c][has_bd], 0.0, None).sum() / bd_sum for c in SPEND_CATS}
cat_sp = {}
for c in SPEND_CATS:
    v = cat_raw[c].copy(); v[~has_bd] = cat_share[c] * sp_total[~has_bd]; cat_sp[c] = v

benefits = (LOUNGE_COST * f["f13"].to_numpy() + f["f14"].to_numpy()
            + 15.0 * f["f15"].to_numpy() + f["f16"].to_numpy())
exp_loss = LGD * f["f11"].to_numpy() * f["f1"].to_numpy()
interest = 0.12 * f["f1"].to_numpy()


def reward_cost(rate_travel_mult=5.0):
    rm = dict(REWARD_MULT); rm["f6"] = rate_travel_mult; rm["f9"] = rate_travel_mult
    return sum(np.clip(cat_sp[c], 0, None) * rm[c] * CPP_POINT for c in SPEND_CATS)


def interchange(rate_travel=0.022, rate_other=0.022):
    travel = cat_sp["f6"] + cat_sp["f9"]; other = cat_sp["f7"] + cat_sp["f8"] + cat_sp["f10"]
    return rate_travel * travel + rate_other * other


print(f"v19 baseline proxy {base:.4f}\n")
print(f"{'variant':<48}{'proxy':>8}{'vs v19':>9}{'Jaccard':>9}")
print("-" * 74)

# A. exactly variant-1 (travel penalized, raw $)
ic = interchange(); rc = reward_cost()
pnl_neg_raw = ic + interest - rc - benefits - exp_loss
report("A. raw-$, travel PENALIZED (=variant1)", apply_f3(pnl_neg_raw))

# B. raw-$, travel NEUTRAL (1x reward like everything else -- isolates the scale-only effect)
rc_neutral = reward_cost(rate_travel_mult=1.0)
pnl_neutral_raw = ic + interest - rc_neutral - benefits - exp_loss
report("B. raw-$, travel NEUTRAL (1x, isolate scale)", apply_f3(pnl_neutral_raw))

# C. raw-$, NO reward cost at all (pure interchange+interest-benefits-loss, all positive)
pnl_allpos_raw = ic + interest - benefits - exp_loss
report("C. raw-$, no reward cost at all (allpos)", apply_f3(pnl_allpos_raw))

# D. raw-$, spend-only (interchange only, no interest/benefits/loss) -- isolate spend-scale vs v19
report("D. raw-$, interchange-only (spend magnitude)", apply_f3(ic))

# E. raw-$, interest-only (isolate f1 magnitude vs v19's z-scored f1)
report("E. raw-$, interest-only (12% x f1, no spend)", apply_f3(interest))

# F. z-scored precise economics (apples-to-apples scale with v19): z(interchange)+z(interest)
#    -z(reward)-z(benefits)-z(exp_loss), travel PENALIZED -- isolates SIGN from SCALE
pnl_neg_z = _z(ic) + _z(interest) - _z(rc) - _z(benefits) - _z(exp_loss)
report("F. z-scored, travel PENALIZED", apply_f3(pnl_neg_z))

# G. z-scored, travel NEUTRAL
pnl_neutral_z = _z(ic) + _z(interest) - _z(rc_neutral) - _z(benefits) - _z(exp_loss)
report("G. z-scored, travel NEUTRAL", apply_f3(pnl_neutral_z))

# H. z-scored, no reward cost (allpos) -- closest structural analog to v15/v19
pnl_allpos_z = _z(ic) + _z(interest) - _z(benefits) - _z(exp_loss)
report("H. z-scored, no reward cost (allpos)", apply_f3(pnl_allpos_z))

# I. z-scored interchange ONLY (spend magnitude, z-scored) vs v19's f7-dominant term
report("I. z-scored, interchange-only", apply_f3(_z(ic)))

# J. z-scored interest ONLY (f1 magnitude, z-scored, exact 12%) vs v19's f1 term
report("J. z-scored, interest-only (12% x f1)", apply_f3(_z(interest)))

print("\n--- diagnosing variant D (interchange-only, raw $) vs v19's f7 weight ---")
print(f"corr(interchange_raw, f7) = {np.corrcoef(ic, f['f7'].to_numpy())[0,1]:.3f}")
print(f"corr(interchange_raw, v19_score) = {np.corrcoef(ic, s19)[0,1]:.3f}")
t_ic = topmask(apply_f3(ic)); t19 = topmask(s19)
print(f"interchange-only top-20% vs v19 top-20%: overlap {(t_ic & t19).sum():,} / 100,000")

print("\n--- variance contribution check: which raw-$ term dominates total variance? ---")
terms = {"interchange": ic, "interest": interest, "reward_cost": rc, "benefits": benefits, "exp_loss": exp_loss}
for k, v in terms.items():
    print(f"  {k:<14} std=${v.std():>12,.0f}  mean=${v.mean():>10,.0f}  range [{v.min():,.0f}, {v.max():,.0f}]")
