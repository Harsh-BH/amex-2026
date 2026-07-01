"""Test whether the f1~f11 inverted-U shape implies v19's expected-loss term (f11*f1) MISCALIBRATES
the high-revolve population, and whether a corrected risk term (or removing it for high-f1) helps."""
import sys; ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA, SPEND_CATS
from score_magnitude import dollar_profit_v19_lending
from lb_predict import LBPredictor, TOP
import numpy as np
import pandas as pd

df = PremierEDA().df
ids = df["id"].to_numpy()
s19 = dollar_profit_v19_lending(df).to_numpy()
p = LBPredictor(ids=ids)
base = p.proxy(s19)
f = df.fillna(0.0)
f1 = f["f1"].to_numpy(); f11 = f["f11"].to_numpy()

# net interest-economics quantity: interest_rev(f1) - expected_loss(f11*f1) = f1*(R_INTEREST - LGD*f11)
# As f11 falls for high f1 (per the inverted-U), the NET margin per revolve-dollar should RISE at the top.
# v19 already adds 0.738*f1 (interest) and -0.110*z(f11*f1) (loss) separately. Let's check: at the TOP
# decile of f1, is the loss term's z-score actually LOWER (less penalty) than at the f11-peak decile (~$3k)?
print("net economics by f1 decile (within f1>0):")
sub = pd.DataFrame({"f1": f1, "f11": f11})
sub_pos = sub[sub["f1"]>0].copy()
sub_pos["bin"] = pd.qcut(sub_pos["f1"], 10, duplicates="drop")
expl_full = -(f11*f1)
sub_pos["expl_z"] = (expl_full[sub_pos.index] - expl_full.mean())/expl_full.std()
g = sub_pos.groupby("bin").agg(f1_mean=("f1","mean"), f11_mean=("f11","mean"), expl_z_mean=("expl_z","mean"))
print(g)
print(f"\n-> if expl_z_mean (the PENALTY, negative=more penalty) gets LESS negative (closer to 0) as f1 rises")
print(f"   past the f11-peak (~$3k), v19 ALREADY correctly captures the inverted-U via the f11*f1 product term.")
print(f"   (f11 falling faster than f1 rises in % terms would need expl=f11*f1 itself to fall, not just z-score)")

print(f"\nraw expl=-(f11*f1) by f1 decile (not z-scored) -- does it actually DECLINE (get less negative) at top f1?")
sub_pos["expl_raw"] = expl_full[sub_pos.index]
print(sub_pos.groupby("bin")["expl_raw"].mean())

print("\n=== test: does REMOVING the risk term entirely for the top-f1 decile help (the 'risk-term over-penalizes high-revolvers' hypothesis)? ===")
top_f1_decile = f1 >= np.percentile(f1[f1>0], 90)
sd = s19.std()
expl_z = -(f11*f1)
expl_z = (expl_z - expl_z.mean())/expl_z.std()
RECOVERED_RISK_W = 0.110
current_risk_contribution = RECOVERED_RISK_W * expl_z
# candidate: zero out the risk penalty ONLY for top-f1-decile members (those are the "wealthy strategic revolver" cohort)
cand = s19 - current_risk_contribution * top_f1_decile.astype(float)  # removes risk term there
cand[f['f3'].to_numpy()==1] = cand.min()-1
pr = p.proxy(cand)
print(f"  remove risk-penalty for top-decile-f1 members: proxy={pr:.4f} delta={pr-base:+.4f}")

# alternative: use a CORRECTED non-monotonic risk multiplier that peaks at f1~3000 and DECAYS at extremes
# i.e. literally substitute in the empirical f11 curve's shape, but that's circular (f11 IS already in the data)
# Real test: is there value in adding an EXTRA bonus for high-f1 (beyond linear) reflecting the lower realized risk?
for boost in [0.05, 0.1, 0.2, 0.3]:
    extra = boost * sd * top_f1_decile.astype(float)
    cand2 = s19 + extra
    cand2[f['f3'].to_numpy()==1] = cand2.min()-1
    pr2 = p.proxy(cand2)
    print(f"  +{boost}*sd bonus for top-decile-f1: proxy={pr2:.4f} delta={pr2-base:+.4f}")
