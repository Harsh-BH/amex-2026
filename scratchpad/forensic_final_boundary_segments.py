"""Final check: are there SEGMENT-SPECIFIC boundary effects -- e.g. within just-in/just-out, does the
share of members with f17-present-f18-missing (business-line anomaly), or f13=3 (lounge 3+), or
f16-saturated differ enough to matter? Catalog every "interesting" derived flag from this session at boundary."""
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

miss = df.isna()
f17_no_f18 = (~miss["f17"]) & (miss["f18"])
f16_sat = (df["f16"].fillna(0).to_numpy() >= 64.0)
f13_3plus = (df["f13"].fillna(0).to_numpy() == 3)
f2f3_indep_distress = (df["f2"].fillna(0).to_numpy()==1) | (df["f3"].fillna(0).to_numpy()==1)

for name, mask in [("f17present_f18missing(biz-line)", f17_no_f18.to_numpy()),
                    ("f16_saturated", f16_sat),
                    ("f13_eq_3(lounge_3plus)", f13_3plus),
                    ("f2_or_f3_distress", f2f3_indep_distress)]:
    rin, rout = mask[just_in].mean(), mask[just_out].mean()
    print(f"  {name}: just-IN={rin:.2%}  just-OUT={rout:.2%}  diff={rin-rout:+.2%}")

print(f"\npopulation baseline rates: f17_no_f18={f17_no_f18.mean():.2%}  f16_sat={f16_sat.mean():.2%}  "
      f"f13_3plus={f13_3plus.mean():.2%}  f2_or_f3={f2f3_indep_distress.mean():.2%}")
