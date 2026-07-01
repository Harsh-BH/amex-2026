"""H3 probe: does the EXACT card economics (problem-brief slide 8 rates) beat v19's z-score proxy,
or add a lever ON TOP of it via a blend?

Exact economics (brief, slide 8):
  - 5x points on flights(f6)/prepaid-hotels(f9); 1x on all else (f7,f8,f10). 1 pt ~ 1.5c.
  - interchange ~2.2% of spend (T&E at-or-above avg discount; retail slightly lower).
  - net interest yield on revolve balance f1 ~12%.
  - credit loss ~ f11 (risk) x f1 (balance) x LGD(0.5).
  - realized reward cost also via f21 (points redeemed) ~1c/pt.
  - benefit credits: f13 lounge ~$35/visit, f14 airline credit $, f15 cab $15/month, f16 ent credit $.

5 things to build, each screened via the validated LB-predictor (NO submission):
  1. Pure precise dollar P&L (5x/1x reward cost @1.5c, 2.2% interchange, 12% interest, benefits, exp loss).
  2. Variant: travel discount rate raised to 3% (travel net-neutral, not negative).
  3. Variant: reward cost from REALIZED redemption f21 (~1c/pt) instead of earned-points category estimate.
  4. KEY: blend = v19 backbone + small weight on the precise per-category NET MARGIN signal.
  5. Verdict table + Jaccard vs v19 + which members the pure P&L mis-ranks (if worse).

Run: .venv/bin/python scratchpad/h3_exacteconomics.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA, SPEND_CATS                                            # noqa: E402
from score_magnitude import (dollar_profit_v19_lending, spend_dollars, _z,        # noqa: E402
                              R_INTEREST, LGD, LOUNGE_COST)
from lb_predict import LBPredictor, TOP                                           # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
df = PremierEDA().df
ids = df["id"].to_numpy()
f = df.fillna(0.0)
N = len(df)

s19 = dollar_profit_v19_lending(df).to_numpy()
f3 = (f["f3"].to_numpy() == 1)
has_bd = df[SPEND_CATS].notna().any(axis=1).to_numpy()

p = LBPredictor(ids=ids)
base = p.proxy(s19)
print(f"v19 baseline: proxy={base:.4f}  predicted-LB={p.predict(s19):.4f}  (actual public LB = 0.859)")
print(f"population: f3=1 {f3.sum():,} ({f3.mean():.1%})  no-breakdown {(~has_bd).sum():,} ({(~has_bd).mean():.1%})\n")


def topmask(score: np.ndarray) -> np.ndarray:
    m = np.zeros(N, bool)
    m[np.argpartition(-score, TOP)[:TOP]] = True
    return m


def jaccard_vs_v19(score: np.ndarray) -> float:
    a, b = topmask(score), topmask(s19)
    return float((a & b).sum()) / float((a | b).sum())


def apply_f3(score: np.ndarray) -> np.ndarray:
    """Standard f3 eviction screen (validated A17 lever), applied to every candidate identically."""
    out = score.copy()
    out[f3] = out.min() - 1.0
    return out


def report(name: str, score: np.ndarray, note: str = "") -> dict:
    pr = p.proxy(score)
    pred = p.predict(score)
    jac = jaccard_vs_v19(score)
    delta = pr - base
    tag = "  <== BEATS v19 (>0.020)" if delta > 0.020 else ("  (gain, sub-noise)" if delta > 0 else "")
    print(f"{name:<42}{pr:>8.4f}{pred:>9.4f}{delta:>+9.4f}{jac:>9.3f}{tag}")
    if note:
        print(f"    {note}")
    return {"name": name, "proxy": pr, "pred_lb": pred, "delta": delta, "jaccard": jac}


# =========================================================================================
# Common building blocks — precise per-category dollar economics from the EXACT brief rates
# =========================================================================================
REWARD_MULT = {"f6": 5.0, "f7": 1.0, "f8": 1.0, "f9": 5.0, "f10": 1.0}   # brief p8: 5x flights/hotels, 1x rest
CPP_POINT = 0.015   # 1.5c midpoint of 1-2c member value per point (issuer EARN cost)
CPP_REDEEM = 0.010  # realized redemption cost ~1c/point (existing CPP constant, used for variant 3)

# spend dollars: breakdown cohort = raw category sums (already $); no-breakdown cohort gets the
# quantile-mapped f5->breakdown-distribution proxy split into categories by the breakdown cohort's
# AVERAGE category mix (so total volume is the validated spend_dollars() proxy, no new assumption
# about the no-breakdown cohort's category SPLIT beyond "average mix").
sp_total = spend_dollars(df).to_numpy()             # validated quantile-mapped total spend, $ (>=0)
cat_raw = {c: np.clip(f[c].to_numpy(), -np.inf, None) for c in SPEND_CATS}   # keep f7 sign (refunds)
cat_share = {}
bd_sum = sum(np.clip(cat_raw[c][has_bd], 0.0, None) for c in SPEND_CATS).sum()
for c in SPEND_CATS:
    cat_share[c] = np.clip(cat_raw[c][has_bd], 0.0, None).sum() / bd_sum if bd_sum else 0.2
print("breakdown-cohort average category mix (used to split no-bd total spend):",
      {k: round(v, 3) for k, v in cat_share.items()})


def per_category_spend(use_no_bd_avgmix: bool = True):
    """Return {cat: $ spend array, len N}, raw for breakdown cohort (sign-preserved on f7),
    average-mix-split of the quantile-mapped total for the no-breakdown cohort."""
    out = {}
    for c in SPEND_CATS:
        v = cat_raw[c].copy()
        if use_no_bd_avgmix:
            v[~has_bd] = cat_share[c] * sp_total[~has_bd]
        else:
            v[~has_bd] = 0.0
        out[c] = v
    return out


def reward_cost(cat_spend: dict, cpp: float) -> np.ndarray:
    """Sum over categories of max(spend,0) x multiplier x cpp — never reward NEGATIVE spend (refunds
    earn no points), but f7 refunds still net into interchange below via the raw (signed) spend."""
    return sum(np.clip(cat_spend[c], 0.0, None) * REWARD_MULT[c] * cpp for c in SPEND_CATS)


def interchange(cat_spend: dict, rate_travel: float, rate_other: float) -> np.ndarray:
    """Interchange = rate x spend, travel(f6,f9) at rate_travel, other(f7,f8,f10) at rate_other.
    f7 refunds (signed) reduce interchange (a refunded sale generates no/negative discount revenue)."""
    travel = sum(cat_spend[c] for c in ("f6", "f9"))
    other = sum(cat_spend[c] for c in ("f7", "f8", "f10"))
    return rate_travel * travel + rate_other * other


def benefits_cost() -> np.ndarray:
    return (LOUNGE_COST * f["f13"].to_numpy() + f["f14"].to_numpy()
            + 15.0 * f["f15"].to_numpy() + f["f16"].to_numpy())          # f15 is MONTHS -> x$15/mo


def expected_loss() -> np.ndarray:
    return LGD * f["f11"].to_numpy() * f["f1"].to_numpy()


def interest_revenue() -> np.ndarray:
    return 0.12 * f["f1"].to_numpy()           # exact 12% net yield per the brief, not v19's R_INTEREST proxy


cat_sp = per_category_spend()
benefits = benefits_cost()
exp_loss = expected_loss()
interest = interest_revenue()

print(f"\n{'variant':<42}{'proxy':>8}{'pred-LB':>9}{'vs v19':>9}{'Jaccard':>9}")
print("-" * 77)

results = []

# =========================================================================================
# VARIANT 1: pure precise dollar P&L — interchange(2.2%) + interest(12%) - reward(5x/1x@1.5c)
#            - benefits - expected_loss
# =========================================================================================
ic1 = interchange(cat_sp, rate_travel=0.022, rate_other=0.022)
rc1 = reward_cost(cat_sp, CPP_POINT)
pnl1 = ic1 + interest - rc1 - benefits - exp_loss
pnl1_screened = apply_f3(pnl1)
results.append(report("1. pure precise $ P&L (2.2%/2.2%, 1.5c)", pnl1_screened))

# diagnostic: how much of the spread comes from travel reward cost exceeding interchange?
travel_sp = cat_sp["f6"] + cat_sp["f9"]
travel_margin_per_dollar = 0.022 - 5.0 * CPP_POINT   # 2.2% - 7.5% = -5.3%
other_margin_per_dollar = 0.022 - 1.0 * CPP_POINT    # 2.2% - 1.5% = +0.7%
print(f"    travel margin/$ = {travel_margin_per_dollar:+.4f} (2.2% ic - 7.5% reward)  "
      f"other margin/$ = {other_margin_per_dollar:+.4f} (2.2% ic - 1.5% reward)")
print(f"    total travel spend $ {travel_sp.sum()/1e9:.2f}B -> reward-cost-exceeds-interchange hole "
      f"${-travel_margin_per_dollar*travel_sp.sum()/1e6:.1f}M")

# =========================================================================================
# VARIANT 2: travel discount rate raised to 3% (closer to net-neutral, not negative)
# =========================================================================================
for rt in (0.030, 0.045, 0.075):
    ic2 = interchange(cat_sp, rate_travel=rt, rate_other=0.022)
    pnl2 = ic2 + interest - rc1 - benefits - exp_loss
    pnl2_screened = apply_f3(pnl2)
    note = ""
    if rt == 0.075:
        note = "(rate_travel=7.5% = exactly cancels the 5x@1.5c reward cost -> travel net-neutral by construction)"
    results.append(report(f"2. travel discount {rt:.1%} (vs 2.2% other)", pnl2_screened, note))

# =========================================================================================
# VARIANT 3: reward cost from REALIZED redemption f21 (~1c/pt) instead of earned-points estimate
# =========================================================================================
realized_cost = CPP_REDEEM * f["f21"].to_numpy()
pnl3 = ic1 + interest - realized_cost - benefits - exp_loss
pnl3_screened = apply_f3(pnl3)
results.append(report("3. reward cost via REALIZED f21 (1c/pt)", pnl3_screened,
                       f"f21 missing for {(df['f21'].isna()).mean():.1%} of pop (filled 0 -> reward cost 0 there)"))

# also: realized cost blended half/half with earned-points estimate (defensible middle)
pnl3b = ic1 + interest - 0.5 * (rc1 + realized_cost) - benefits - exp_loss
results.append(report("3b. reward cost 50/50 earned+realized", apply_f3(pnl3b)))

print()

# =========================================================================================
# VARIANT 4 (KEY): blend = v19 z-score backbone + small weight on precise per-category NET MARGIN
# =========================================================================================
# Build the "net margin" signal: per-category (interchange_rate - reward_rate) x spend, summed.
# This is the SAME structure as pnl1's revenue side but WITHOUT interest/benefits/exp_loss (those
# are already represented inside v19 via its own f1 lending term and risk term) -- isolates the
# ONE genuinely new lever the brief's exact rates add: precise reward-vs-interchange CATEGORY MARGIN.
net_margin = sum((0.022 - REWARD_MULT[c] * CPP_POINT) * cat_sp[c] for c in SPEND_CATS)
net_margin_z = _z(net_margin)

print(f"net_margin diagnostics: mean ${net_margin.mean():,.0f}  std ${net_margin.std():,.0f}  "
      f"corr(net_margin, v19) Pearson={np.corrcoef(net_margin, s19)[0,1]:.3f}  "
      f"Spearman={pd.Series(net_margin).corr(pd.Series(s19), method='spearman'):.3f}\n")

print(f"{'blend weight w':<42}{'proxy':>8}{'pred-LB':>9}{'vs v19':>9}{'Jaccard':>9}")
print("-" * 77)
peak_blend = (base, 0.0, None)
for w in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.80, 1.0):
    blended = s19 + w * net_margin_z * s19.std()      # match v19's own scale before adding
    blended_screened = apply_f3(blended)
    r = report(f"4. v19 + w={w:.2f}*z(net_margin)", blended_screened)
    if r["proxy"] > peak_blend[0]:
        peak_blend = (r["proxy"], w, r)
print(f"  peak blend: w={peak_blend[1]:.2f}  proxy={peak_blend[0]:.4f}  delta={peak_blend[0]-base:+.4f}  "
      f"{'CONFIDENT (>0.02)' if peak_blend[0]-base > 0.020 else 'within noise / no gain'}\n")

# Variant 4b: same blend idea but ONLY the travel-vs-other ASYMMETRY (a single signed dummy-like
# signal: margin differential, not full net_margin) -- tests if just "penalize travel a bit" helps
travel_asym = (cat_sp["f6"] + cat_sp["f9"]) * (0.022 - 5.0 * CPP_POINT) \
            + (cat_sp["f7"] + cat_sp["f8"] + cat_sp["f10"]) * 0.0   # only travel penalty, other untouched
travel_asym_z = _z(travel_asym)
print(f"{'blend weight w (travel-only)':<42}{'proxy':>8}{'pred-LB':>9}{'vs v19':>9}{'Jaccard':>9}")
print("-" * 77)
peak_asym = (base, 0.0)
for w in (0.0, 0.05, 0.10, 0.20, 0.35, 0.50):
    blended = s19 + w * travel_asym_z * s19.std()
    r = report(f"4b. v19 + w={w:.2f}*z(travel_penalty_only)", apply_f3(blended))
    if r["proxy"] > peak_asym[0]:
        peak_asym = (r["proxy"], w)
print(f"  peak: w={peak_asym[1]:.2f}  delta={peak_asym[0]-base:+.4f}  "
      f"{'CONFIDENT' if peak_asym[0]-base > 0.020 else 'within noise / no gain'}\n")


# =========================================================================================
# VARIANT 5: full diagnostic — verdict + mis-ranking analysis for the pure $ P&L (variant 1)
# =========================================================================================
print("=" * 77)
print("VERDICT DIAGNOSTICS — variant 1 (pure precise $ P&L) vs v19")
print("=" * 77)
t1 = topmask(pnl1_screened); t19 = topmask(s19)
demoted = t19 & ~t1   # in v19 top-20%, NOT in pure-P&L top-20%
promoted = t1 & ~t19  # in pure-P&L top-20%, NOT in v19 top-20%
print(f"v19 top-20%: {t19.sum():,}  pure-P&L top-20%: {t1.sum():,}  overlap: {(t1&t19).sum():,}  "
      f"Jaccard {jaccard_vs_v19(pnl1_screened):.3f}")
print(f"demoted by pure P&L (in v19, not in P&L): {demoted.sum():,}")
print(f"promoted by pure P&L (in P&L, not in v19): {promoted.sum():,}\n")

def profile(mask, label):
    idx = np.where(mask)[0]
    if len(idx) == 0:
        print(f"  {label}: (empty)")
        return
    sub_travel = (cat_sp["f6"][idx] + cat_sp["f9"][idx])
    sub_other = (cat_sp["f7"][idx] + cat_sp["f8"][idx] + cat_sp["f10"][idx])
    sub_f1 = f["f1"].to_numpy()[idx]
    sub_risk = f["f11"].to_numpy()[idx]
    sub_nobd = (~has_bd)[idx].mean()
    print(f"  {label} (n={len(idx):,}): median travel-spend ${np.median(sub_travel):,.0f}  "
          f"other-spend ${np.median(sub_other):,.0f}  f1(balance) ${np.median(sub_f1):,.0f}  "
          f"risk f11 {np.median(sub_risk):.3f}  no-bd {sub_nobd:.1%}")

profile(demoted, "DEMOTED by pure P&L")
profile(promoted, "PROMOTED by pure P&L")
profile(t19 & t1, "STABLE (in both)")

print(f"\nReward-cost share check: total reward cost (5x/1x@1.5c) = ${rc1.sum()/1e6:.1f}M  "
      f"total interchange (2.2%) = ${ic1.sum()/1e6:.1f}M  net = ${(ic1.sum()-rc1.sum())/1e6:.1f}M")
travel_cost_share = (5.0 * CPP_POINT * np.clip(cat_sp["f6"]+cat_sp["f9"], 0, None)).sum() / rc1.sum()
print(f"travel (5x) categories drive {travel_cost_share:.1%} of total reward cost despite being "
      f"{(np.clip(cat_sp['f6']+cat_sp['f9'],0,None).sum())/(np.clip(cat_sp['f6'],0,None)+np.clip(cat_sp['f7'],0,None)+np.clip(cat_sp['f8'],0,None)+np.clip(cat_sp['f9'],0,None)+np.clip(cat_sp['f10'],0,None)).sum().sum():.1%} of spend volume")

print("\n" + "=" * 77)
print("SUMMARY TABLE")
print("=" * 77)
print(f"{'variant':<42}{'proxy':>8}{'pred-LB':>9}{'vs v19':>9}{'Jaccard':>9}{'verdict':>14}")
for r in results:
    verdict = "BEATS (>0.02)" if r["delta"] > 0.020 else ("gain<noise" if r["delta"] > 0 else "worse")
    print(f"{r['name']:<42}{r['proxy']:>8.4f}{r['pred_lb']:>9.4f}{r['delta']:>+9.4f}{r['jaccard']:>9.3f}{verdict:>14}")
print(f"{'4. peak blend w='+str(peak_blend[1]):<42}{peak_blend[0]:>8.4f}{'':>9}{peak_blend[0]-base:>+9.4f}"
      f"{'':>9}{'BEATS' if peak_blend[0]-base>0.020 else 'gain<noise' if peak_blend[0]-base>0 else 'worse':>14}")
