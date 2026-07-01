"""Forensic Thread 4: BOUNDARY PROFILE. v19 rank 90K-100K (just-IN) vs 100K-110K (just-OUT).
Check EVERY raw feature + derived ratios/interactions/missingness-flags/2nd-order for systematic difference."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
import numpy as np
import pandas as pd

df = PremierEDA().df.copy()
s19 = dollar_profit_v19_lending(df).to_numpy()
order = np.argsort(-s19, kind="stable")

just_in = order[90_000:100_000]
just_out = order[100_000:110_000]
print(f"just-IN n={len(just_in)}  just-OUT n={len(just_out)}")
print(f"score range just-IN: [{s19[just_in].min():.4f}, {s19[just_in].max():.4f}]")
print(f"score range just-OUT: [{s19[just_out].min():.4f}, {s19[just_out].max():.4f}]")

def cmp(name, vec_in, vec_out, fmt=".4f"):
    mi, mo = np.nanmean(vec_in), np.nanmean(vec_out)
    si, so = np.nanstd(vec_in), np.nanstd(vec_out)
    medi, medo = np.nanmedian(vec_in), np.nanmedian(vec_out)
    ratio = mi/mo if mo not in (0, np.nan) and not np.isnan(mo) else float('nan')
    # also a t-stat-like effect size: diff / pooled std
    pooled = np.sqrt((si**2+so**2)/2) + 1e-12
    eff = (mi-mo)/pooled
    flag = "  <<<<" if abs(eff) > 0.05 else ("  <<" if abs(eff) > 0.02 else "")
    print(f"  {name:<28} in_mean={mi:{fmt}} out_mean={mo:{fmt}} ratio={ratio:.3f} in_med={medi:{fmt}} out_med={medo:{fmt}} effsize={eff:+.4f}{flag}")

FEATS = [f"f{i}" for i in range(1, 24)]
print("\n=== A. raw features (re-verify A19, with finer effect-size lens) ===")
for c in FEATS:
    v = df[c].to_numpy(float)
    cmp(c, v[just_in], v[just_out])

print("\n=== B. missingness FLAGS (does presence/absence differ, not just value-when-present?) ===")
for c in FEATS:
    m = df[c].isna().to_numpy(float)
    cmp(f"{c}_ISMISSING", m[just_in], m[just_out], fmt=".4f")

print("\n=== C. derived ratios / interactions ===")
f = df.fillna(0.0)
catsum = f[SPEND_CATS].sum(axis=1).to_numpy()
f5 = f["f5"].to_numpy(); f1 = f["f1"].to_numpy(); f4 = f["f4"].to_numpy(); f21 = f["f21"].to_numpy()
f11 = f["f11"].to_numpy(); f17 = f["f17"].to_numpy(); f7 = f["f7"].to_numpy(); f10=f["f10"].to_numpy()
f6=f["f6"].to_numpy(); f8=f["f8"].to_numpy(); f9=f["f9"].to_numpy()
f12=f["f12"].to_numpy(); f19=f["f19"].to_numpy(); f20=f["f20"].to_numpy()
f13=f["f13"].to_numpy(); f14=f["f14"].to_numpy(); f15=f["f15"].to_numpy(); f16=f["f16"].to_numpy()
f22=f["f22"].to_numpy(); f23=f["f23"].to_numpy()

derived = {
    "redemption_intensity=f21/(f4+f21)": np.divide(f21, f4+f21, out=np.zeros_like(f21), where=(f4+f21)>0),
    "f7_share_of_catsum": np.divide(f7, catsum, out=np.zeros_like(f7), where=catsum>0),
    "f10_share_of_catsum": np.divide(f10, catsum, out=np.zeros_like(f10), where=catsum>0),
    "f6_share_of_catsum (airline)": np.divide(f6, catsum, out=np.zeros_like(f6), where=catsum>0),
    "f9_share_of_catsum (lodging)": np.divide(f9, catsum, out=np.zeros_like(f9), where=catsum>0),
    "travel_share=(f6+f9)/catsum": np.divide(f6+f9, catsum, out=np.zeros_like(f6), where=catsum>0),
    "spend_diversity(HHI)": (np.divide(f6,catsum,out=np.zeros_like(f6),where=catsum>0)**2 +
                              np.divide(f7,catsum,out=np.zeros_like(f7),where=catsum>0)**2 +
                              np.divide(f8,catsum,out=np.zeros_like(f8),where=catsum>0)**2 +
                              np.divide(f9,catsum,out=np.zeros_like(f9),where=catsum>0)**2 +
                              np.divide(f10,catsum,out=np.zeros_like(f10),where=catsum>0)**2),
    "revolve_to_lend=f1/f17": np.divide(f1, f17, out=np.zeros_like(f1), where=f17>0),
    "utilization_proxy=f1/(f17+1)": f1/(f17+1),
    "risk_adj_balance=f11*f1": f11*f1,
    "risk_per_spend=f11/(catsum+1)": f11/(catsum+1),
    "spend_per_login=catsum/(f12+1)": catsum/(f12+1),
    "engagement=f12+f22": f12+f22,
    "supp_density=catsum/f19": catsum/np.maximum(f19,1),
    "benefit_burden=f14+f15*15+f16": f14+f15*15+f16,
    "benefit_to_spend=(f14+f15*15+f16)/(catsum+1)": (f14+f15*15+f16)/(catsum+1),
    "rewards_per_spend=f4/(catsum+1)": f4/(catsum+1),
    "cancel_x_risk=f2*f11": f["f2"].to_numpy()*f11,
    "f1_x_f11(expected loss)": f1*f11,
    "catsum_x_(1-f11)": catsum*(1-f11),
    "log1p_catsum": np.log1p(catsum),
    "sqrt_catsum": np.sqrt(catsum),
    "f4_over_f17": np.divide(f4, f17, out=np.zeros_like(f4), where=f17>0),
    "f12_x_f22(engagement interaction)": f12*f22,
    "lounge_to_spend=f13/(catsum+1)": f13/(catsum+1),
    "n_active_benefits=(f13>0)+(f14>0)+(f15>0)+(f16>0)": (f13>0).astype(float)+(f14>0)+(f15>0)+(f16>0),
    "n_spend_cats_active": (f6>0).astype(float)+(f7>0)+(f8>0)+(f9>0)+(f10>0),
    "email_engagement=f22*f23": f22*f23,
    "f19_x_f20": f19*f20,
    "f2_or_f3(any_distress)": np.maximum(f["f2"].to_numpy(), f["f3"].to_numpy()),
}
for name, vec in derived.items():
    cmp(name, vec[just_in], vec[just_out])

print("\n=== D. SECOND-ORDER: variance/skew within each band per feature (do tails differ even if means match?) ===")
for c in ["f1","f7","f4","f11","catsum"]:
    if c == "catsum":
        v = catsum
    else:
        v = df[c].fillna(0).to_numpy(float)
    pin, pout = np.percentile(v[just_in], [10,50,90,99]), np.percentile(v[just_out], [10,50,90,99])
    print(f"  {c}: in pct(10/50/90/99)={pin.round(1)}  out pct={pout.round(1)}")
