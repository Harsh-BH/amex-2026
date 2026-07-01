"""Thread 4c: a few more boundary-band derived feature probes not in the prior 23 -- specifically
combos of missingness with the VALUE side, and absolute-vs-relative position features."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
import numpy as np
import pandas as pd

df = PremierEDA().df
s19 = dollar_profit_v19_lending(df).to_numpy()
order = np.argsort(-s19, kind="stable")
just_in = order[90_000:100_000]
just_out = order[100_000:110_000]

def cmp(name, vec_in, vec_out):
    mi, mo = np.nanmean(vec_in), np.nanmean(vec_out)
    si, so = np.nanstd(vec_in), np.nanstd(vec_out)
    pooled = np.sqrt((si**2+so**2)/2) + 1e-12
    eff = (mi-mo)/pooled
    flag = "  <<<<" if abs(eff) > 0.05 else ("  <<" if abs(eff) > 0.02 else "")
    print(f"  {name:<40} in={mi:.4f} out={mo:.4f} effsize={eff:+.4f}{flag}")

f = df.fillna(0.0)
catsum = f[SPEND_CATS].sum(axis=1).to_numpy()
f1 = f["f1"].to_numpy(); f4=f["f4"].to_numpy(); f11=f["f11"].to_numpy(); f17=f["f17"].to_numpy()
f6=f["f6"].to_numpy(); f7=f["f7"].to_numpy(); f8=f["f8"].to_numpy(); f9=f["f9"].to_numpy(); f10=f["f10"].to_numpy()
miss = df.isna()

print("=== A. interactions between missingness FLAGS and the value of an UNRELATED feature ===")
# e.g. does rewards-missing interact with how much they revolve?
derived = {
    "f1_if_rewards_missing": f1 * miss["f4"].to_numpy(float),
    "f1_if_rewards_present": f1 * (~miss["f4"]).to_numpy(float),
    "catsum_if_lendline_missing": catsum * miss["f17"].to_numpy(float),
    "catsum_if_lendline_present": catsum * (~miss["f17"]).to_numpy(float),
    "f7_minus_f10 (other vs dining gap)": f7 - f10,
    "f6_minus_f9 (airline vs lodging gap)": f6 - f9,
    "category_count_weighted_by_amt(max_share)": np.max(np.column_stack([f6,f7,f8,f9,f10]), axis=1) / np.maximum(catsum,1),
    "f4_minus_f21(unredeemed_balance)": f4 - f["f21"].to_numpy(),
    "abs(f17-f18)(business_vs_consumer_gap)": np.abs(f17 - f["f18"].to_numpy()),
    "f11_x_catsum(risk-weighted_spend, raw not 1-f11)": f11*catsum,
    "rank_of_f1_within_revolvers": np.nan, # placeholder, computed below
    "is_top_decile_f7": (f7 >= np.percentile(f7,90)).astype(float),
    "is_top_decile_f1": (f1 >= np.percentile(f1,90)).astype(float),
    "n_features_at_cap(censored)": ((df["f5"]>=13596).astype(float) + (df["f17"].fillna(0)>=63800).astype(float)),
}
for name, vec in derived.items():
    if name == "rank_of_f1_within_revolvers":
        continue
    cmp(name, vec[just_in], vec[just_out])

print("\n=== B. is the boundary driven by CENSORING (values pinned at the data max = artificial cap)? ===")
caps = {"f5": 13596.2799, "f17": 63800, "f18": 54800, "f6": 52198, "f7": 146701, "f9": 10829, "f10": 21651, "f1": 17967.726330}
for c, cap in caps.items():
    v = df[c].fillna(0).to_numpy(float)
    near_cap = (v >= cap*0.999)
    print(f"  {c} near-cap({cap}) rate: just-IN={near_cap[just_in].mean():.3%}  just-OUT={near_cap[just_out].mean():.3%}")
