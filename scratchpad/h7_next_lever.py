"""Hunt the NEXT predictor-blind lever past v22 (0.866), using v19->v22 as a known-good compass.

The LB-predictor is blind to basis/form changes, so I screen with what I CAN trust:
  (1) WHALE PROTECTION — the 15,721 f7-whales must stay ~0.999 in-rate (demoting them = the v6/v8 loss).
  (2) GRADIENT COMPASS — v19(0.859)->v22(0.866) is a KNOWN-GOOD direction. A variant that overlaps v22
      MORE than v19, and whose fresh members match the PROFILE of v22's winning additions (low specialty
      spike, broad spend), is pushing further the right way. A variant that reverts toward v19 is not.
  (3) defensible economics + non-degenerate + f3 evicted.
Run: .venv/bin/python scratchpad/h7_next_lever.py
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd

ROOT = "/home/harsh1/github-repos/amex-2026"; sys.path.insert(0, ROOT + "/src")
from eda import PremierEDA                                          # noqa: E402
from score_magnitude import dollar_profit_v19_lending, dollar_profit_v22_hybrid  # noqa: E402
from lb_predict import TOP                                         # noqa: E402

df = PremierEDA().df
f = df.fillna(0.0)
f3 = (f["f3"].to_numpy() == 1)
SMALL = ["f8", "f10", "f6", "f9"]                                  # rank-normalized in v22
whale = (f["f1"].to_numpy() == 0) & (f["f7"].to_numpy() > np.quantile(f["f7"].to_numpy(), 0.95))


def _zc(v):
    v = np.asarray(v, float); return v / (v.std() + 1e-9)


def _rank(v):
    return pd.Series(np.asarray(v, float)).rank(pct=True).to_numpy()


def topset(s):
    return set(np.argsort(-np.asarray(s))[:TOP])


s19 = dollar_profit_v19_lending(df).to_numpy()
s22 = dollar_profit_v22_hybrid(df).to_numpy()
t19, t22 = topset(s19), topset(s22)
gain_in = t22 - t19          # v22's winning PROMOTIONS (these reclassifications gained +0.007)
gain_out = t19 - t22         # v22's winning DEMOTIONS
# profile of v22's winning additions (what the good direction looks like)
gin = np.array(sorted(gain_in))
print(f"v19->v22 moved {len(gain_in):,} in / {len(gain_out):,} out (+0.007). "
      f"winning-ADD profile: catsum {f.loc[gin,SMALL].sum(1).median():.0f}, f7 {f.loc[gin,'f7'].median():.0f}, "
      f"f1 {f.loc[gin,'f1'].median():.0f}")


def compass(name, s):
    t = topset(s)
    jac22 = len(t & t22) / len(t | t22)
    ov22 = len(t & t22) / TOP
    ov19 = len(t & t19) / TOP
    wr = np.mean([i in t for i in np.where(whale)[0]])
    # gradient alignment: of the members this variant moves vs v22, do they CONTINUE v22's winning direction?
    new_in = t - t22                       # this variant promotes (beyond v22)
    new_out = t22 - t                      # this variant demotes (vs v22)
    # continue-right = new demotions look like gain_out profile (high specialty spike), new promotions like gain_in
    align = "?"
    if new_in and new_out:
        ni, no = np.array(sorted(new_in)), np.array(sorted(new_out))
        spike_out = f.loc[no, SMALL].max(1).median()      # demoted: are they specialty-spikers? (good if high)
        spike_in = f.loc[ni, SMALL].max(1).median()       # promoted: broader? (good if lower)
        align = f"demote-spike {spike_out:.0f} vs promote-spike {spike_in:.0f} ({'CONTINUES v22' if spike_out > spike_in else 'reverts'})"
    print(f"  {name:<22} ov22 {ov22:.3f} ov19 {ov19:.3f} | whale {wr:.3f} | distinct {len(set(np.round(s,6))):>7,} | {align}")


print(f"\ncompass (ov22>ov19 & whale~0.999 & 'CONTINUES v22' = pushing the winning direction further):")
compass("v19 (baseline)", s19)
compass("v22 (current best)", s22)


def hybrid(small_transform):
    """v22 spine but apply `small_transform` to the 4 specialty cats; f7/f1 stay dollar/std."""
    sc = 0.738 * _zc(f["f7"].to_numpy()) + 0.738 * _zc(f["f1"].to_numpy())
    for k, wv in {"f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}.items():
        sc = sc + wv * _zc(small_transform(f[k].to_numpy()))
    sc = sc + 0.110 * _zc(-(f["f11"].to_numpy() * f["f1"].to_numpy()))
    sc[f3] = sc.min() - 1.0
    return sc


# --- variants, all whale-safe by construction (f7/f1 untouched on dollar basis) ---
compass("v24 winsor97.5 small", hybrid(lambda v: np.minimum(v, np.quantile(v, 0.975))))
compass("v25 rank^0.5 (compress+)", hybrid(lambda v: _rank(v) ** 0.5))
compass("v26 rank^2 (toward raw)", hybrid(lambda v: _rank(v) ** 2))
compass("v27 binarize>median", hybrid(lambda v: (v > np.median(v[v > 0])).astype(float) if (v > 0).any() else v * 0))
# multiplicative both-engines: v22 spend x (1 + lending); whales have f1=0 so factor=1 (protected)
def mult(lam):
    spend = 0.738 * _zc(f["f7"].to_numpy())
    for k, wv in {"f8": 0.348, "f10": 0.137, "f6": 0.060, "f9": 0.060}.items():
        spend = spend + wv * _zc(_rank(f[k].to_numpy()))
    spend = spend - spend.min() + 0.1                       # shift positive so the multiplier is meaningful
    sc = spend * (1.0 + lam * _rank(f["f1"].to_numpy())) + 0.738 * _zc(f["f1"].to_numpy())
    sc = sc + 0.110 * _zc(-(f["f11"].to_numpy() * f["f1"].to_numpy()))
    sc[f3] = sc.min() - 1.0
    return sc
compass("v28 mult both-engine .5", mult(0.5))
compass("v29 mult both-engine 1.0", mult(1.0))
