"""H_benefitpos probe: is BENEFIT UTILIZATION a POSITIVE profitability signal (engaged/sticky/
high-income member), not just a cost?

Context: the official problem statement names FOUR drivers — spend behavior, revolving patterns,
riskiness, AND benefit utilization. v19 (locked best, LB 0.859) uses only the first three; benefit
features (f13-f16) only ever appear as a COST (A29/h1_costside.py: H1b "absolute benefit cost"
subtracted from v19 peaked at w=0.05 for +0.0004 -- 50x below the 0.020 noise floor, i.e. flat/dead
as a NEGATIVE term). This probe tests the OPPOSITE sign: benefit utilization ADDED as a positive
engagement signal. Never tested before.

BENEFIT_FEATS = f13 Lounge Access Count, f14 Airline Credits used, f15 Cab benefit months,
f16 Entertainment Credit Used Amount. Co-miss together (13,716 rows) -- the natural reading of
missing is "no benefit usage data / not a benefit user" = 0, tested explicitly (encoding 1 below
also tests treating missing as "unknown" via a separate flag, to be thorough).

5 ENCODINGS (each added as +w*z(term) to v19, screened via the validated LB-predictor, f3-screen
always re-applied AFTER adding the term):
  E1 benefit BREADTH      -- count of {f13,f14,f15,f16} nonzero (0-4)
  E2 benefit MAGNITUDE    -- z(f13+f14+f15+f16) raw sum (f15 in MONTHS, mixed units -- documented)
  E3 benefit FLAGS        -- binary "uses any benefit" (E3a) and "uses 3+ benefits" (E3b)
  E4 benefit INTENSITY    -- benefit usage PER DOLLAR of spend (engaged-relative-to-wallet)
  E5 benefit×SPEND interaction -- breadth/magnitude multiplied onto spend (benefit users get a
     spend-MULTIPLIER, i.e. "engaged members convert spend to more profit") -- the closest read of
     "benefit users are MORE profitable" rather than additively more profitable.

Run: .venv/bin/python scratchpad/h_benefitpos.py
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from eda import PremierEDA                                          # noqa: E402
from score_magnitude import dollar_profit_v19_lending, spend_dollars, _z  # noqa: E402
from lb_predict import LBPredictor                                  # noqa: E402

df = PremierEDA().df
ids = df["id"].to_numpy()
f = df.fillna(0.0)
s19 = dollar_profit_v19_lending(df).to_numpy()
f3 = (f["f3"].to_numpy() == 1)

p = LBPredictor(ids=ids)
base = p.proxy(s19)
NOISE_FLOOR = 0.020
print(f"v19 baseline proxy {base:.4f}  predicted-LB {p.predict(s19):.4f}  (actual 0.859)\n")

BEN = ["f13", "f14", "f15", "f16"]
ben_nan = df[BEN].isna().all(axis=1).to_numpy()
print(f"benefit co-miss rows: {ben_nan.sum():,} ({ben_nan.mean():.1%} of pop) -- treated as 0 usage (natural reading)\n")

f13, f14, f15, f16 = (f[c].to_numpy() for c in BEN)
spend = spend_dollars(df).to_numpy()


def screen(name: str, term: np.ndarray, weights=(0.0, 0.05, 0.10, 0.20, 0.35, 0.50, 0.80, 1.20)):
    """Standard sweep: candidate = s19 + w*z(term), f3-screen re-applied, proxy + predicted-LB printed."""
    print(f"{name}   (ADD w * z(term) to v19, re-apply f3 screen):")
    print(f"{'w':>7}{'proxy':>9}{'pred-LB':>9}{'vs v19':>9}")
    zt = _z(term)
    peak = (base, 0.0)
    for w in weights:
        cand = s19 + w * zt
        cand[f3] = cand.min() - 1.0
        pr = p.proxy(cand)
        tag = "  <==" if pr > peak[0] else ""
        print(f"{w:>7.2f}{pr:>9.4f}{p.predict(cand):>9.4f}{pr-base:>+9.4f}{tag}")
        if pr > peak[0]:
            peak = (pr, w)
    delta = peak[0] - base
    verdict = "CONFIDENT WIN (>0.02)" if delta > NOISE_FLOOR else ("positive but sub-noise" if delta > 0 else "no gain / hurts")
    print(f"  peak: w={peak[1]:.2f}  proxy={peak[0]:.4f}  delta={delta:+.4f}  -> {verdict}\n")
    return peak[1], delta, verdict


results = {}

# --- E1: benefit BREADTH (count of distinct benefits used, 0-4) ---
breadth = (f13 > 0).astype(float) + (f14 > 0).astype(float) + (f15 > 0).astype(float) + (f16 > 0).astype(float)
print(f"E1 breadth distribution: {pd.Series(breadth).value_counts().sort_index().to_dict()}")
results["E1_breadth"] = screen("E1 benefit BREADTH (count nonzero of f13,f14,f15,f16)", breadth)

# --- E2: benefit MAGNITUDE (total usage sum, raw mixed units, documented) ---
magnitude = f13 + f14 + f15 + f16
results["E2_magnitude"] = screen("E2 benefit MAGNITUDE (f13+f14+f15+f16 raw sum)", magnitude)

# --- E3a/E3b: binary flags ---
any_benefit = (breadth >= 1).astype(float)
three_plus = (breadth >= 3).astype(float)
print(f"E3a 'any benefit' positive rate: {any_benefit.mean():.1%}")
print(f"E3b '3+ benefits' positive rate: {three_plus.mean():.1%}")
results["E3a_any"] = screen("E3a binary 'uses ANY premium benefit'", any_benefit)
results["E3b_3plus"] = screen("E3b binary 'uses 3+ benefits' (high engagement)", three_plus)

# --- E4: benefit INTENSITY relative to spend (usage per dollar of wallet) ---
# stabilize denominator with the median nonzero spend (same pattern as h1_costside.py's `burden`)
med_spend = np.median(spend[spend > 0])
intensity = magnitude / (spend + med_spend)
results["E4_intensity"] = screen("E4 benefit INTENSITY (usage / (spend + median_spend))", intensity)

# --- E5: benefit x SPEND interaction (engaged members convert spend to MORE value) ---
# breadth as a 0-4 engagement multiplier scaling z(spend); centered so breadth=0 is neutral (no boost)
breadth_centered = breadth - breadth.mean()
interaction = breadth_centered * _z(spend)
results["E5_interaction"] = screen("E5 benefit-engagement x SPEND interaction (breadth_c * z(spend))", interaction)

# --- Also test: treat co-missing f13-f16 as a distinct "unknown" flag rather than 0-usage ---
# (the prompt notes missing=0 is the natural reading but asks us to also test it explicitly)
unknown_flag = ben_nan.astype(float)
print(f"E_unknown: testing the co-miss flag itself (orthogonal check, not a benefit-utilization claim)")
results["E_unknown_flag"] = screen("E_unknown (f13-f16 co-miss flag, ADDED positive -- sanity check)", unknown_flag)

print("\n" + "=" * 78)
print("SUMMARY (peak weight, proxy delta vs v19, verdict):")
print(f"{'encoding':<22}{'peak w':>8}{'delta':>10}{'verdict':>26}")
for k, (w, d, v) in results.items():
    print(f"{k:<22}{w:>8.2f}{d:>+10.4f}{v:>26}")
best_k = max(results, key=lambda k: results[k][1])
print(f"\nBEST encoding: {best_k}  delta={results[best_k][1]:+.4f}  ({results[best_k][2]})")
