"""Retrodiction grading of the two research-round-3 hypotheses (H1 attrition-dampener,
H2 mid-risk hump / risk-step) against all 7 measured swap outcomes.

H1 (BankChurners structure): attrition tracks low activity, not balances -> penalize
    static-balance disengaged members. Signal (higher = better member):
    s = -( pr(f1) * (1 - pr(engagement)) )
H2a (IMF hump): mid-risk revolvers are the profit sweet spot -> s = pr(f1) * window(f11)
H2b (UCI step): risk is a step at the extreme tail, not a slope -> s = 1 - (f11 > q97)
Reference rows: pu_hgb (current champion), margin, random.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
K = 100_000
RNG = np.random.default_rng(23)

z = np.load(ROOT / "scratchpad" / "tri2_cache.npz", allow_pickle=False)
names = [str(x) for x in z["names"]]
df = pd.read_pickle(ROOT / "data" / "premier.pkl").sort_values("id").reset_index(drop=True)
assert np.array_equal(df["id"].to_numpy(), z["ids"])
ids = df["id"].to_numpy()

w6 = np.load(ROOT / "scratchpad" / "tri2_fit6_w.npy")
SIX = [names.index(n) for n in ("z1", "z7", "z9", "z10", "exl", "f3neg")]
margin = (z["T"][:, SIX] @ w6.astype(np.float32)).astype(np.float64)


def pr(v):
    return pd.Series(v).rank(pct=True).to_numpy()


f1 = df["f1"].fillna(0).to_numpy()
f11 = df["f11"].fillna(0).to_numpy()
eng = (pr(df["f12"].fillna(0).to_numpy()) + pr(df["f22"].fillna(0).to_numpy())) / 2
nz = f11[f11 > 0]
q60, q95, q97 = np.quantile(nz, [0.60, 0.95, 0.97])
sig_npz = np.load(ROOT / "scratchpad" / "tiebreak_signals.npz")

SIGNALS = {
    "H1_attr_damp": pr(-(pr(f1) * (1 - eng))),
    "H2a_midrisk_rev": pr(pr(f1) * ((f11 >= q60) & (f11 <= q95)).astype(float)),
    "H2b_risk_step": pr(1.0 - (f11 > q97).astype(float)),
    "pu_hgb_REF": sig_npz["pu_hgb"].astype(np.float64),
    "margin_REF": pr(margin),
    "random_REF": pr(RNG.standard_normal(len(df))),
}

PAIRS = [("v33", "v29", -0.611), ("v34", "v29", +0.50), ("v35", "v34", +0.074),
         ("v36", "v35", -0.252), ("v37L", "v35", +0.034), ("v30", "v29", -0.310),
         ("v41", "v35", -0.076)]


def topset(v):
    s = pd.read_csv(ROOT / "data" / f"scores_{v}.csv").set_index("id")["score"].reindex(ids).to_numpy()
    m = np.zeros(len(s), bool)
    m[np.argpartition(-s, K)[:K]] = True
    return m


sets = {v: topset(v) for v in {p for pair in PAIRS for p in pair[:2]}}
print(f"{'pair':>10} {'net':>7} |" + "".join(f"{s:>17}" for s in SIGNALS))
preds = {s: [] for s in SIGNALS}
nets = []
for probe, base, net in PAIRS:
    IN = sets[probe] & ~sets[base]
    OUT = sets[base] & ~sets[probe]
    nets.append(net)
    row = f"{probe+'|'+base:>10} {net:>+7.3f} |"
    for s, sig in SIGNALS.items():
        d = float(sig[IN].mean() - sig[OUT].mean())
        preds[s].append(d)
        row += f"{d:>+17.3f}"
    print(row)

nets_a = np.array(nets)
print(f"\n{'signal':>16} {'sign-hits':>10} {'spearman':>9}   (n=7 — qualitative; grade vs the REF rows)")
for s in SIGNALS:
    p = np.array(preds[s])
    hits = int((np.sign(p) == np.sign(nets_a)).sum())
    rho = spearmanr(p, nets_a).statistic
    print(f"{s:>16} {hits:>7}/7 {rho:>+9.3f}")
